#api/app/services/chat/factory.py
from services.chat.types import ChatServiceEnum

# ✅ 반환 타입을 명시하여 코드 안정성을 높입니다.
from services.chat.base import BaseChatService
from typing import Type


def get_chat(chat_type: ChatServiceEnum) -> Type[BaseChatService]:
    # # 뇌절 AI (temporarily disabled)
    # if chat_type == ChatServiceEnum.BRAIN_CRASH:
    #     from services.chat.braincrash_chat_model.chat_service import BrainCrashChatService
    #     return BrainCrashChatService

    # 알파 AI
    if chat_type == ChatServiceEnum.ALPHA_AI:
        from services.chat.alpha_ai_model.chat_service import AlphaAIChatService
        return AlphaAIChatService

    raise ValueError("Invalid Chat Service Type")