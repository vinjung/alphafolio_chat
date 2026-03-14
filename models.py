#api/app/models.py
from pydantic import BaseModel
from typing import Optional, Dict, Any
from core.llm.types import LLMProvider
from services.chat.types import ChatServiceEnum

class ChatRequest(BaseModel):
    message: str = "삼성전자 투자해도 될까?"
    provider: LLMProvider = LLMProvider.ANTHROPIC
    model: str = "claude-sonnet-4-6"
    max_tokens: Optional[int] = 4000
    # 프론트엔드에서 받은 서비스 타입을 이 필드로 받습니다.
    chat_service_type: ChatServiceEnum = ChatServiceEnum.ALPHA_AI
    # 히스토리 관리를 위한 필드
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    # Compatibility methods (same interface as api ChatRequest)
    def get_provider(self) -> LLMProvider:
        return self.provider

    def get_model(self) -> str:
        return self.model

    def get_chat_service_type(self) -> ChatServiceEnum:
        return self.chat_service_type

class ChatResponse(BaseModel):
    response: str
    usage: Optional[Dict[str, Any]] = None
    model: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
