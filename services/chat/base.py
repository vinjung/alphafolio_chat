#api/app/services/chat/base.py
import os
import inspect
from abc import ABC
from services.chat.types import ChatServiceEnum
from core.llm.factory import LLMProvider, get_llm
from config import logger
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from typing import Optional, Any


class BaseChatService(ABC):
    chat_type: ChatServiceEnum
    main_llm: BaseChatModel
    messages: list[BaseMessage]
    graph_state: dict[str, Any]

    def __init__(
            self,
            provider: LLMProvider = LLMProvider.ANTHROPIC,
            model_name: Optional[str] = None,
            session_id: str = None,  # ToDO Implement session.
            **llm_config
    ):
        # main_llm은 graph node에서 생성하므로 여기서는 생성하지 않음 (중복 방지)
        # self.main_llm = get_llm(provider, model_name, **llm_config)
        self.graph_state = {
            "provider": provider,  # 수정: 파라미터 provider 사용 (하드코딩 제거)
            "model_name": model_name,
            "model_config": llm_config,
            "messages": []
        }

    def get_session(self, session_id):
        self.messages = []
        logger.warn('Warning: Session not implemented yet. Chat history is not preserved.')

    def load_prompt(self, file_name: str) -> str:
        # 정의된 class에서
        caller_file = inspect.getfile(self.__class__)
        base_dir = os.path.dirname(os.path.abspath(caller_file))
        file_path = os.path.join(base_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def invoke(self, query: str, state: dict[str, Any] = None) -> str:
        raise NotImplemented

    async def ainvoke(self, query: str, state: dict[str, Any] = None) -> str:
        raise NotImplemented

    def stream(self, query: str, state: dict[str, Any] = None) -> str:
        raise NotImplemented

    async def astream(self, query: str, state: dict[str, Any] = None) -> str:
        raise NotImplemented

    async def astream(self, request):
        """실제 Langchain astream 구현"""
        try:
            system_prompt = self.load_prompt('prompts/system_prompt.md')
            from datetime import date

            formatted_prompt = system_prompt.format(
                TODAY=date.today().isoformat(),
                USER_QUERY=request.message
            )

            # Langchain astream 사용
            async for chunk in self.main_llm.astream(formatted_prompt):
                yield chunk

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
