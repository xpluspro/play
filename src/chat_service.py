from langchain_community.chat_models.tongyi import ChatTongyi
from langchain.schema import HumanMessage, SystemMessage
import os

from pydantic import SecretStr
from models import GAME_PROMPTS


class QwenChatService:
    def __init__(self):
        self.api_key = os.getenv("QWEN_API_KEY")

        if not self.api_key:
            raise ValueError("QWEN_API_KEY environment variable not set.")

        self.client = ChatTongyi(
            model="qwen-turbo",
            api_key=SecretStr(self.api_key),
        )

    def get_response_sync(self, message: str, game_id: str) -> str:
        """获取AI回复"""
        try:
            game_prompt = GAME_PROMPTS.get(game_id)
            if not game_prompt:
                return "游戏不存在"

            messages = [
                SystemMessage(content=game_prompt.system_prompt),
                HumanMessage(content=message),
            ]

            # Use the synchronous `invoke` method
            response = self.client.invoke(messages)
            content: str = response.content
            return content.strip().replace(game_prompt.answer, "███")

        except Exception as e:
            print(f"AI response error: {e}")
            return "抱歉，我现在无法回答，请稍后再试。"

    def check_answer(self, guess: str, game_id: str) -> bool:
        """检查答案是否正确"""
        game_prompt = GAME_PROMPTS.get(game_id)
        if not game_prompt:
            return False

        # Simple answer matching
        return (
            guess.strip().lower() == game_prompt.answer.lower()
            or game_prompt.answer.lower() in guess.strip().lower()
        )
