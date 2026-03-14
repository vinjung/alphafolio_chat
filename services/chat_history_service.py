"""
Chat History Service
대화 히스토리 관리 서비스
작성일: 2025-10-08
"""

import asyncpg
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from config import logger


class ChatHistoryService:
    """대화 히스토리 관리 서비스"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def create_session(
        self,
        user_id: Optional[str],
        chat_service_type: str,
        title: str = "New Chat",
        llm_provider: str = "anthropic",
        llm_model: str = "claude-sonnet-4-6"
    ) -> str:
        """새 대화 세션 생성"""
        async with self.db_pool.acquire() as conn:
            session_id = await conn.fetchval(
                """
                INSERT INTO chat_sessions
                (user_id, title, chat_service_type, llm_provider, llm_model)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                user_id,
                title,
                chat_service_type,
                llm_provider,
                llm_model
            )
            logger.info(f"[ChatHistory] New session created: {session_id}")
            return str(session_id)

    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """세션의 메시지 히스토리 조회 (LangChain 형식으로 변환)"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    role,
                    content,
                    created_at,
                    tokens_used,
                    model_used,
                    tools_used,
                    processing_time_ms
                FROM chat_messages
                WHERE session_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                UUID(session_id),
                limit
            )

            messages = []
            for row in rows:
                messages.append({
                    'id': str(row['id']),
                    'role': row['role'],
                    'content': row['content'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'tokens_used': row['tokens_used'],
                    'model_used': row['model_used'],
                    'tools_used': row['tools_used'],
                    'processing_time_ms': row['processing_time_ms']
                })

            logger.info(f"[ChatHistory] Retrieved {len(messages)} messages for session {session_id}")
            return messages

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None,
        tools_used: Optional[Dict] = None,
        processing_time_ms: Optional[int] = None,
        visualization: Optional[Dict] = None
    ) -> str:
        """메시지 추가"""
        async with self.db_pool.acquire() as conn:
            # Convert dict fields to JSON strings for database storage
            tools_used_str = json.dumps(tools_used) if tools_used else None
            visualization_str = json.dumps(visualization) if visualization else None

            message_id = await conn.fetchval(
                """
                INSERT INTO chat_messages
                (session_id, role, content, tokens_used, model_used, tools_used, processing_time_ms, visualization)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                UUID(session_id),
                role,
                content,
                tokens_used,
                model_used,
                tools_used_str,
                processing_time_ms,
                visualization_str
            )
            logger.info(f"[ChatHistory] Message added: {message_id} (role={role})")
            return str(message_id)

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    id,
                    user_id,
                    title,
                    chat_service_type,
                    created_at,
                    updated_at,
                    last_message_at,
                    message_count,
                    llm_provider,
                    llm_model,
                    is_archived,
                    is_pinned
                FROM chat_sessions
                WHERE id = $1
                """,
                UUID(session_id)
            )

            if not row:
                return None

            return {
                'id': str(row['id']),
                'user_id': row['user_id'],
                'title': row['title'],
                'chat_service_type': row['chat_service_type'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                'last_message_at': row['last_message_at'].isoformat() if row['last_message_at'] else None,
                'message_count': row['message_count'],
                'llm_provider': row['llm_provider'],
                'llm_model': row['llm_model'],
                'is_archived': row['is_archived'],
                'is_pinned': row['is_pinned']
            }

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        chat_service_type: Optional[str] = None,
        limit: int = 20,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """세션 목록 조회"""
        conditions = []
        params = []
        param_count = 0

        if user_id:
            param_count += 1
            conditions.append(f"user_id = ${param_count}")
            params.append(user_id)

        if chat_service_type:
            param_count += 1
            conditions.append(f"chat_service_type = ${param_count}")
            params.append(chat_service_type)

        if not include_archived:
            conditions.append("is_archived = FALSE")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        param_count += 1
        params.append(limit)

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT
                    id,
                    user_id,
                    title,
                    chat_service_type,
                    created_at,
                    updated_at,
                    message_count,
                    is_pinned
                FROM chat_sessions
                WHERE {where_clause}
                ORDER BY is_pinned DESC, updated_at DESC
                LIMIT ${param_count}
                """,
                *params
            )

            sessions = []
            for row in rows:
                sessions.append({
                    'id': str(row['id']),
                    'user_id': row['user_id'],
                    'title': row['title'],
                    'chat_service_type': row['chat_service_type'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'message_count': row['message_count'],
                    'is_pinned': row['is_pinned']
                })

            return sessions

    async def update_session_title(self, session_id: str, title: str):
        """세션 제목 업데이트"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE chat_sessions
                SET title = $1, updated_at = NOW()
                WHERE id = $2
                """,
                title,
                UUID(session_id)
            )
            logger.info(f"[ChatHistory] Session title updated: {session_id}")

    async def archive_session(self, session_id: str):
        """세션 아카이브"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE chat_sessions
                SET is_archived = TRUE, updated_at = NOW()
                WHERE id = $1
                """,
                UUID(session_id)
            )
            logger.info(f"[ChatHistory] Session archived: {session_id}")

    async def delete_session(self, session_id: str):
        """세션 삭제 (CASCADE로 메시지도 함께 삭제)"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM chat_sessions
                WHERE id = $1
                """,
                UUID(session_id)
            )
            logger.info(f"[ChatHistory] Session deleted: {session_id}")

    async def convert_messages_to_langchain_format(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """
        세션 메시지를 LangChain 형식으로 변환

        Returns:
            [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
                ...
            ]
        """
        messages = await self.get_session_messages(session_id, limit)

        langchain_messages = []
        for msg in messages:
            if msg['role'] in ['user', 'assistant', 'system']:
                langchain_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })

        return langchain_messages
