import redis.asyncio as redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
from models import GameSession
import os

class SessionManager:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1小时
    
    async def connect(self):
        """连接Redis"""
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
    
    async def create_session(self, game_id: str) -> str:
        """创建新的游戏会话"""
        session_id = str(uuid.uuid4())
        session = GameSession(
            session_id=session_id,
            game_id=game_id,
            start_time=datetime.now()
        )
        
        # 存储到Redis
        await self.redis_client.setex(
            f"session:{session_id}",
            self.session_timeout,
            session.model_dump_json()
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[GameSession]:
        """获取会话信息"""
        session_data = await self.redis_client.get(f"session:{session_id}")
        if session_data:
            return GameSession.model_validate_json(session_data)
        return None
    
    async def update_session(self, session: GameSession):
        """更新会话信息"""
        await self.redis_client.setex(
            f"session:{session.session_id}",
            self.session_timeout,
            session.model_dump_json()
        )
    
    async def delete_session(self, session_id: str):
        """删除会话"""
        await self.redis_client.delete(f"session:{session_id}")
    
    async def add_message(self, session_id: str, role: str, content: str):
        """添加消息到会话"""
        session = await self.get_session(session_id)
        if session:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            session.messages.append(message)
            await self.update_session(session)
    
    async def increment_attempts(self, session_id: str) -> int:
        """增加尝试次数"""
        session = await self.get_session(session_id)
        if session:
            session.attempts += 1
            await self.update_session(session)
            return session.attempts
        return 0
    
    async def finish_game(self, session_id: str):
        """完成游戏"""
        session = await self.get_session(session_id)
        if session:
            session.is_finished = True
            await self.update_session(session)
    
    async def get_game_time(self, session_id: str) -> Optional[float]:
        """获取游戏耗时（秒）"""
        session = await self.get_session(session_id)
        if session:
            return (datetime.now() - session.start_time).total_seconds()
        return None
