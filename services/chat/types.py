#api/app/services/chat/types.py
from enum import Enum


class ChatServiceEnum(Enum):
    # BRAIN_CRASH = "BRAIN_CRASH"  # 뇌절 AI (엔터테인먼트) - temporarily disabled
    ALPHA_AI = "ALPHA_AI"        # 알파 AI (Text-to-SQL 특화)
