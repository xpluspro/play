from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import asyncio
from datetime import datetime
from typing import Dict, List
import json
import uuid

from models import GAME_PROMPTS, GuessRequest, GuessResponse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 简单的内存会话存储（仅用于开发测试）
sessions: Dict[str, Dict] = {}

app = FastAPI(title="猜东西游戏")

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
    
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "game_id": game_id,
        "start_time": datetime.now(),
        "attempts": 0,
        "is_finished": False,
        "messages": []
    }
    
    return {
        "session_id": session_id,
        "game_name": GAME_PROMPTS[game_id].name,
        "max_attempts": GAME_PROMPTS[game_id].max_attempts
    }

@app.post("/api/guess")
async def make_guess(request: GuessRequest):
    """提交猜测"""
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[request.session_id]
    if session["is_finished"]:
        raise HTTPException(status_code=400, detail="游戏已结束")
    
    game_prompt = GAME_PROMPTS[session["game_id"]]
    session["attempts"] += 1
    
    # 记录用户消息
    session["messages"].append({
        "role": "user",
        "content": request.guess,
        "timestamp": datetime.now().isoformat()
    })
    
    # 简单的答案检查
    def check_answer(guess: str, game_id: str) -> bool:
        game_prompt = GAME_PROMPTS.get(game_id)
        if not game_prompt:
            return False
        return guess.strip().lower() == game_prompt.answer.lower() or game_prompt.answer in guess
    
    is_correct = check_answer(request.guess, session["game_id"])
    
    if is_correct:
        # 答案正确
        session["is_finished"] = True
        elapsed_time = (datetime.now() - session["start_time"]).total_seconds()
        
        response = GuessResponse(
            message=f"🎉 恭喜你答对了！答案就是：{game_prompt.answer}",
            is_correct=True,
            game_over=True,
            attempts_left=0,
            elapsed_time=elapsed_time
        )
    elif session["attempts"] >= game_prompt.max_attempts:
        # 尝试次数用完
        session["is_finished"] = True
        response = GuessResponse(
            message=f"很遗憾，你的尝试次数已用完。正确答案是：{game_prompt.answer}",
            is_correct=False,
            game_over=True,
            attempts_left=0
        )
    else:
        # 继续游戏，给出简单回复
        if "是" in request.guess or "?" in request.guess:
            ai_response = "很好的问题！让我想想... 不完全是这样的，再试试其他问题吧！"
        else:
            ai_response = "嗯，这个猜测不太对。试试问一些关于特征的问题，比如颜色、大小、用途等。"
        
        session["messages"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        response = GuessResponse(
            message=ai_response,
            is_correct=False,
            game_over=False,
            attempts_left=game_prompt.max_attempts - session["attempts"]
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
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session = sessions[session_id]
    elapsed_time = (datetime.now() - session["start_time"]).total_seconds()
    
    return {
        "messages": session["messages"],
        "attempts": session["attempts"],
        "is_finished": session["is_finished"],
        "elapsed_time": elapsed_time
    }

if __name__ == "__main__":
    print("🎮 启动猜东西游戏服务器...")
    print("📝 注意：这是简化版本，使用内存存储会话数据")
    print("🌐 访问: http://localhost:8000")
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
