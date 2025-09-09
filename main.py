from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import asyncio
from datetime import datetime
from typing import Dict, List
import json
from contextlib import asynccontextmanager

from models import GAME_PROMPTS, GuessRequest, GuessResponse
from chat_service import QwenChatService
from session_manager import SessionManager
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(json.dumps(message))

# 全局变量
chat_service = QwenChatService()
session_manager = SessionManager()
connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时连接Redis
    await session_manager.connect()
    yield
    # 关闭时的清理工作
    pass

app = FastAPI(title="猜东西游戏", lifespan=lifespan)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    """主页 - 游戏选择页面"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/game/{game_id}")
async def game_page(game_id: str):
    """游戏页面"""
    if game_id not in GAME_PROMPTS:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    with open("static/game.html", "r", encoding="utf-8") as f:
        content = f.read()
        # 替换游戏ID
        content = content.replace("{{GAME_ID}}", game_id)
        content = content.replace("{{GAME_NAME}}", GAME_PROMPTS[game_id].name)
        return HTMLResponse(content=content)

@app.get("/api/games")
async def get_games():
    """获取所有游戏列表"""
    games = []
    for game_id, prompt in GAME_PROMPTS.items():
        games.append({
            "id": game_id,
            "name": prompt.name,
            "max_attempts": prompt.max_attempts,
            "hints_count": len(prompt.hints)
        })
    return games

@app.post("/api/start_game/{game_id}")
async def start_game(game_id: str):
    """开始新游戏"""
    if game_id not in GAME_PROMPTS:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    session_id = await session_manager.create_session(game_id)
    return {
        "session_id": session_id,
        "game_name": GAME_PROMPTS[game_id].name,
        "max_attempts": GAME_PROMPTS[game_id].max_attempts
    }

@app.post("/api/guess")
async def make_guess(request: GuessRequest):
    """提交猜测"""
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if session.is_finished:
        raise HTTPException(status_code=400, detail="游戏已结束")
    
    game_prompt = GAME_PROMPTS[session.game_id]
    attempts = await session_manager.increment_attempts(request.session_id)
    
    # 记录用户消息
    await session_manager.add_message(request.session_id, "user", request.guess)
    
    # 检查答案
    is_correct = chat_service.check_answer(request.guess, session.game_id)
    
    if is_correct:
        # 答案正确
        await session_manager.finish_game(request.session_id)
        elapsed_time = await session_manager.get_game_time(request.session_id)
        
        response = GuessResponse(
            message=f"🎉 恭喜你答对了！答案就是：{game_prompt.answer}",
            is_correct=True,
            game_over=True,
            attempts_left=0,
            elapsed_time=elapsed_time
        )
    elif attempts >= game_prompt.max_attempts and game_prompt.max_attempts < 999:
        # 尝试次数用完（只有在设置了有效限制时才判断）
        await session_manager.finish_game(request.session_id)
        response = GuessResponse(
            message=f"很遗憾，你的尝试次数已用完。正确答案是：{game_prompt.answer}",
            is_correct=False,
            game_over=True,
            attempts_left=0
        )
    else:
        # 继续游戏，获取AI回复
        ai_response = await chat_service.get_response(request.guess, session.game_id)
        await session_manager.add_message(request.session_id, "assistant", ai_response)
        
        response = GuessResponse(
            message=ai_response,
            is_correct=False,
            game_over=False,
            attempts_left=game_prompt.max_attempts - attempts if game_prompt.max_attempts < 999 else -1  # -1 表示无限制
        )
    
    return response

@app.get("/api/hints/{game_id}")
async def get_hints(game_id: str):
    """获取游戏提示"""
    if game_id not in GAME_PROMPTS:
        raise HTTPException(status_code=404, detail="游戏不存在")
    
    return {"hints": GAME_PROMPTS[game_id].hints}

@app.get("/api/session/{session_id}/history")
async def get_chat_history(session_id: str):
    """获取聊天历史"""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return {
        "messages": session.messages,
        "attempts": session.attempts,
        "is_finished": session.is_finished,
        "elapsed_time": await session_manager.get_game_time(session_id)
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket连接用于实时通信"""
    await connection_manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 这里可以处理实时消息，比如typing指示器
            if message.get("type") == "ping":
                await connection_manager.send_message(session_id, {"type": "pong"})
                
    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # 支持多进程
        loop="asyncio"
    )
