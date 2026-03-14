"""
Chat History API Router
대화 히스토리 관리 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from services.chat.session_manager import (
    SessionManager,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageResponse
)
from database import db
from config import logger

router = APIRouter(prefix="/chat/history", tags=["Chat History"])


# =====================================================
# Dependency
# =====================================================
def get_session_manager() -> SessionManager:
    """SessionManager 싱글톤"""
    if not db.pool:
        raise HTTPException(500, "Database not connected")
    return SessionManager(db.pool)


# =====================================================
# 세션 관리 API
# =====================================================
@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    data: ChatSessionCreate,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    새 대화 세션 생성

    - **user_id**: 사용자 ID (필수)
    - **chat_service_type**: AI 타입 (ALPHA, SKYROCKET, BRAIN_CRASH)
    - **title**: 대화 제목 (선택, 없으면 첫 메시지로 자동 생성)
    """
    try:
        session = await manager.create_session(data)
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(500, f"Failed to create session: {str(e)}")


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    user_id: str = Query(..., description="사용자 ID"),
    limit: int = Query(50, ge=1, le=100, description="조회 개수"),
    include_archived: bool = Query(False, description="아카이브 포함 여부"),
    manager: SessionManager = Depends(get_session_manager)
):
    """
    사용자의 대화 세션 목록 조회

    - 최신순 정렬
    - 고정된 세션이 최상단
    """
    try:
        sessions = await manager.get_user_sessions(user_id, limit, include_archived)
        return sessions
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(500, f"Failed to get sessions: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """세션 상세 조회"""
    session = await manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session


@router.get("/sessions/{session_id}/limit")
async def check_session_limit(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    세션 메시지/토큰 제한 상태 조회

    Returns:
        - can_continue: 추가 메시지 가능 여부
        - current_messages: 현재 메시지 수
        - max_messages: 최대 메시지 수
        - remaining_messages: 남은 메시지 수
        - current_tokens: 현재 토큰 사용량
        - max_tokens: 최대 토큰 수
        - remaining_tokens: 남은 토큰 수
        - limit_reason: 제한 도달 시 사유 (message_limit / token_limit)
    """
    try:
        limit_info = await manager.check_session_limit(session_id)
        return {
            "success": True,
            "session_id": session_id,
            **limit_info
        }
    except Exception as e:
        logger.error(f"Failed to check session limit: {e}")
        raise HTTPException(500, str(e))


@router.get("/sessions/{session_id}/full")
async def get_session_with_limit(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    세션 상세 + 제한 정보 조회

    세션 정보와 함께 메시지/토큰 제한 상태를 반환합니다.
    """
    try:
        result = await manager.get_session_with_limit_info(session_id)
        if not result:
            raise HTTPException(404, "Session not found")
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session with limit: {e}")
        raise HTTPException(500, str(e))


@router.patch("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str = Query(..., min_length=1, max_length=500),
    manager: SessionManager = Depends(get_session_manager)
):
    """세션 제목 수정"""
    try:
        await manager.update_session_title(session_id, title)
        return {"success": True, "message": "Title updated"}
    except Exception as e:
        logger.error(f"Failed to update title: {e}")
        raise HTTPException(500, str(e))


@router.post("/sessions/{session_id}/pin")
async def toggle_pin(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """세션 고정/해제"""
    try:
        new_state = await manager.toggle_pin(session_id)
        return {
            "success": True,
            "is_pinned": new_state,
            "message": "Pinned" if new_state else "Unpinned"
        }
    except Exception as e:
        logger.error(f"Failed to toggle pin: {e}")
        raise HTTPException(500, str(e))


@router.post("/sessions/{session_id}/archive")
async def archive_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """세션 아카이브"""
    try:
        await manager.archive_session(session_id)
        return {"success": True, "message": "Session archived"}
    except Exception as e:
        logger.error(f"Failed to archive session: {e}")
        raise HTTPException(500, str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """세션 삭제"""
    try:
        await manager.delete_session(session_id)
        return {"success": True, "message": "Session deleted"}
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(500, str(e))


# =====================================================
# 메시지 관리 API
# =====================================================
@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    limit: int = Query(100, ge=1, le=500, description="조회 개수"),
    manager: SessionManager = Depends(get_session_manager)
):
    """
    세션의 메시지 목록 조회

    - 시간순 정렬 (오래된 것부터)
    - user/assistant 메시지 포함
    """
    try:
        messages = await manager.get_session_messages(session_id, limit)
        return messages
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(500, str(e))


# =====================================================
# 통계 API
# =====================================================
@router.get("/users/{user_id}/stats")
async def get_user_stats(
    user_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """
    사용자 통계

    - 전체 세션 수
    - 전체 메시지 수
    - 사용한 토큰 수
    - 활동 일수
    """
    try:
        stats = await manager.get_user_stats(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        raise HTTPException(500, str(e))


# =====================================================
# Health Check
# =====================================================
@router.get("/health")
async def history_health_check():
    """대화 히스토리 시스템 상태"""
    try:
        # DB 연결 확인
        async with db.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
