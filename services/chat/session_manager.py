"""
Chat Session Manager
대화 히스토리 관리 (Claude PC 스타일)
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from config import logger, settings
from services.chat.types import ChatServiceEnum


# =====================================================
# Helper Functions
# =====================================================
def get_model_id(chat_service_type: ChatServiceEnum) -> str:
    """ChatServiceEnum을 model_id로 매핑"""
    MODEL_MAPPING = {
        ChatServiceEnum.ALPHA_AI: "stock-ai"
    }
    return MODEL_MAPPING.get(chat_service_type, "stock-ai")


def get_chat_service_type(model_id: str) -> ChatServiceEnum:
    """model_id를 ChatServiceEnum으로 역매핑"""
    REVERSE_MAPPING = {
        "stock-ai": ChatServiceEnum.ALPHA_AI,
        "alpha-ai": ChatServiceEnum.ALPHA_AI
    }
    return REVERSE_MAPPING.get(model_id, ChatServiceEnum.ALPHA_AI)


# =====================================================
# Pydantic Models (기존 chat_sessions 테이블 구조에 맞춤)
# =====================================================
class ChatSessionCreate(BaseModel):
    """세션 생성 요청"""
    user_id: str
    model_id: str = "alpha-ai"  # stock-ai, brain-ai, alpha-ai
    title: Optional[str] = None


class ChatSessionResponse(BaseModel):
    """세션 응답 (기존 테이블 구조)"""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    model_id: str


class ChatMessageCreate(BaseModel):
    """메시지 생성 요청 (기존 테이블 구조에 맞춤)"""
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    visualization: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    """메시지 응답 (기존 테이블 구조에 맞춤)"""
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime
    visualization: Optional[Dict[str, Any]] = None


# =====================================================
# Session Manager
# =====================================================
class SessionManager:
    """대화 히스토리 관리자"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    # -------------------------------------------------
    # 세션 관리
    # -------------------------------------------------
    async def create_session(self, data: ChatSessionCreate) -> ChatSessionResponse:
        """새 대화 세션 생성 (기존 테이블 구조 사용)"""
        session_id = str(uuid.uuid4())
        title = data.title or "새 대화"  # 기본 제목

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_sessions
                (id, user_id, title, model_id)
                VALUES ($1, $2, $3, $4)
            """, session_id, data.user_id, title, data.model_id)

            row = await conn.fetchrow("""
                SELECT * FROM chat_sessions WHERE id = $1
            """, session_id)

        logger.info(f"[SessionManager] Created session: {session_id} (model: {data.model_id})")

        # Convert UUID objects to strings for Pydantic
        row_dict = dict(row)
        row_dict['id'] = str(row_dict['id'])
        row_dict['user_id'] = str(row_dict['user_id'])
        return ChatSessionResponse(**row_dict)

    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[ChatSessionResponse]:
        """사용자의 세션 목록 조회 (최신순, 기존 테이블 구조)"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM chat_sessions
                WHERE user_id = $1
                ORDER BY updated_at DESC
                LIMIT $2
            """, user_id, limit)

        # Convert UUID objects to strings
        sessions = []
        for row in rows:
            row_dict = dict(row)
            row_dict['id'] = str(row_dict['id'])
            row_dict['user_id'] = str(row_dict['user_id'])
            sessions.append(ChatSessionResponse(**row_dict))

        logger.info(f"[SessionManager] Found {len(sessions)} sessions for user: {user_id}")
        return sessions

    async def get_session(self, session_id: str) -> Optional[ChatSessionResponse]:
        """세션 상세 조회 (기존 테이블 구조)"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM chat_sessions WHERE id = $1
            """, session_id)

        if row:
            row_dict = dict(row)
            row_dict['id'] = str(row_dict['id'])
            row_dict['user_id'] = str(row_dict['user_id'])
            return ChatSessionResponse(**row_dict)
        return None

    async def update_session_title(self, session_id: str, title: str):
        """세션 제목 수정 (기존 테이블 구조)"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE chat_sessions
                SET title = $1, updated_at = NOW()
                WHERE id = $2
            """, title, session_id)

        logger.info(f"[SessionManager] Updated session title: {session_id}")

    async def delete_session(self, session_id: str):
        """세션 삭제 (CASCADE로 메시지도 삭제)"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM chat_sessions WHERE id = $1
            """, session_id)

        logger.info(f"[SessionManager] Deleted session: {session_id}")

    # -------------------------------------------------
    # 메시지 관리
    # -------------------------------------------------
    async def save_message(self, data: ChatMessageCreate) -> ChatMessageResponse:
        """메시지 저장 (기존 테이블 구조)"""
        import json
        message_id = str(uuid.uuid4())
        visualization_str = json.dumps(data.visualization) if data.visualization else None

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO chat_messages
                (id, session_id, role, content, visualization)
                VALUES ($1, $2, $3, $4, $5)
            """, message_id, data.session_id, data.role, data.content, visualization_str)

            row = await conn.fetchrow("""
                SELECT id, session_id, role, content, created_at, visualization
                FROM chat_messages WHERE id = $1
            """, message_id)

        logger.info(f"[SessionManager] Saved message: {message_id} ({data.role})")

        # Convert UUID objects to strings and parse JSON fields
        row_dict = dict(row)
        row_dict['id'] = str(row_dict['id'])
        row_dict['session_id'] = str(row_dict['session_id'])
        if row_dict.get('visualization') and isinstance(row_dict['visualization'], str):
            import json
            row_dict['visualization'] = json.loads(row_dict['visualization'])
        return ChatMessageResponse(**row_dict)

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ChatMessageResponse]:
        """세션의 메시지 목록 조회 (시간순)"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, session_id, role, content, created_at, visualization
                FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at ASC
                LIMIT $2
            """, session_id, limit)

        # Convert UUID objects to strings and parse JSON fields
        import json
        messages = []
        for row in rows:
            row_dict = dict(row)
            row_dict['id'] = str(row_dict['id'])
            row_dict['session_id'] = str(row_dict['session_id'])
            if row_dict.get('visualization') and isinstance(row_dict['visualization'], str):
                row_dict['visualization'] = json.loads(row_dict['visualization'])
            messages.append(ChatMessageResponse(**row_dict))

        logger.info(f"[SessionManager] Found {len(messages)} messages for session: {session_id}")
        return messages

    async def get_messages_as_langchain(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[BaseMessage]:
        """LangChain 메시지 형식으로 변환"""
        messages_data = await self.get_session_messages(session_id, limit)

        langchain_messages = []
        for msg in messages_data:
            if msg.role == 'user':
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == 'assistant':
                langchain_messages.append(AIMessage(content=msg.content))

        return langchain_messages

    # -------------------------------------------------
    # 통계
    # -------------------------------------------------
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """사용자 통계"""
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(DISTINCT s.id) as total_sessions,
                    COUNT(m.id) as total_messages,
                    SUM(COALESCE(m.tokens_used, 0)) as total_tokens,
                    COUNT(DISTINCT DATE(s.created_at)) as active_days
                FROM chat_sessions s
                LEFT JOIN chat_messages m ON s.id = m.session_id
                WHERE s.user_id = $1
            """, user_id)

        return dict(stats)

    # -------------------------------------------------
    # Session Limit Management
    # -------------------------------------------------
    async def check_session_limit(self, session_id: str) -> Dict[str, Any]:
        """
        Check if session has reached message/token limits

        Args:
            session_id: Session ID to check

        Returns:
            Dict with limit status:
            - can_continue: bool - whether more messages can be sent
            - current_messages: int - current message count
            - max_messages: int - maximum allowed messages
            - remaining_messages: int - messages remaining
            - current_tokens: int - current token usage
            - max_tokens: int - maximum allowed tokens
            - remaining_tokens: int - tokens remaining
            - limit_reason: str or None - reason if limit reached
        """
        max_messages = settings.MAX_MESSAGES_PER_SESSION
        max_tokens = settings.MAX_TOKENS_PER_SESSION

        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as message_count,
                    COALESCE(SUM(COALESCE(tokens_used, 0)), 0) as total_tokens
                FROM chat_messages
                WHERE session_id = $1
            """, session_id)

        current_messages = stats['message_count'] if stats else 0
        current_tokens = int(stats['total_tokens']) if stats else 0

        remaining_messages = max(0, max_messages - current_messages)
        remaining_tokens = max(0, max_tokens - current_tokens)

        # Determine if limit is reached and why
        limit_reason = None
        can_continue = True

        if current_messages >= max_messages:
            can_continue = False
            limit_reason = "message_limit"
        elif current_tokens >= max_tokens:
            can_continue = False
            limit_reason = "token_limit"

        result = {
            "can_continue": can_continue,
            "current_messages": current_messages,
            "max_messages": max_messages,
            "remaining_messages": remaining_messages,
            "current_tokens": current_tokens,
            "max_tokens": max_tokens,
            "remaining_tokens": remaining_tokens,
            "limit_reason": limit_reason
        }

        if not can_continue:
            logger.info(f"[SessionManager] Session {session_id} limit reached: {limit_reason}")

        return result

    async def get_session_with_limit_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session details including limit information

        Args:
            session_id: Session ID

        Returns:
            Dict with session info and limit status, or None if not found
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        limit_info = await self.check_session_limit(session_id)

        return {
            "session": session.model_dump(),
            "limit_info": limit_info
        }
