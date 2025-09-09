from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from typing import AsyncGenerator
import asyncio
import httpx
from models import GAME_PROMPTS

class QwenChatService:
    def __init__(self):
        self.api_key = os.getenv("QWEN_API_KEY")
        self.base_url = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        self.client = ChatOpenAI(
            model_name="qwen-turbo",
            temperature=0.3,
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            max_tokens=200
        )
    
    async def get_response(self, message: str, game_id: str) -> str:
        """获取AI回复"""
        try:
            game_prompt = GAME_PROMPTS.get(game_id)
            if not game_prompt:
                return "游戏不存在"
            
            messages = [
                SystemMessage(content=game_prompt.system_prompt),
                HumanMessage(content=message)
            ]
            
            response = await asyncio.to_thread(self.client.invoke, messages)
            return response.content.strip()
            
        except Exception as e:
            print(f"AI response error: {e}")
            return "抱歉，我现在无法回答，请稍后再试。"
    
    def check_answer(self, guess: str, game_id: str) -> bool:
        """检查答案是否正确"""
        game_prompt = GAME_PROMPTS.get(game_id)
        if not game_prompt:
            return False
        
        # 简单的答案匹配，可以扩展为更智能的匹配
        return guess.strip().lower() == game_prompt.answer.lower() or game_prompt.answer in guess
