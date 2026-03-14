"""
Chat API with Session Integration
세션 관리가 통합된 채팅 API

기존 /chat/stream을 대체하여 자동으로 세션에 메시지 저장
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import json
import time
import uuid

from models import ChatRequest
from services.chat.factory import get_chat
from services.chat.base import BaseChatService
# from services.redis_stream_service import redis_stream_service  # Redis removed
from services.chat.session_manager import SessionManager, ChatMessageCreate
from config import logger, settings
from database import db

router = APIRouter()


# =====================================================
# Request Model (세션 ID 추가)
# =====================================================
class ChatRequestWithSession(BaseModel):
    """세션 ID가 포함된 채팅 요청"""
    message: str = Field(..., description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID (없으면 새로 생성)")
    user_id: str = Field(..., description="사용자 ID")

    # 기존 ChatRequest 필드
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    max_tokens: Optional[int] = 4000
    chat_service_type: str = "ALPHA"


# =====================================================
# Dependency
# =====================================================
def get_session_manager() -> SessionManager:
    """SessionManager 의존성"""
    if not db.pool:
        raise HTTPException(500, "Database not connected")
    return SessionManager(db.pool)


def get_dynamic_chat_service(request: ChatRequestWithSession) -> BaseChatService:
    """동적 Chat Service 인스턴스 생성"""
    from services.chat.types import ChatServiceEnum
    try:
        service_type = ChatServiceEnum(request.chat_service_type)
        service_class = get_chat(service_type)
        return service_class(provider=request.provider, model_name=request.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat service type: {str(e)}")


# =====================================================
# 통합 스트리밍 API
# =====================================================
@router.post("/chat/stream-with-history")
async def chat_stream_with_history(
    request: ChatRequestWithSession,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    세션 관리가 통합된 채팅 API

    **Flow**:
    1. session_id 없으면 → 새 세션 생성
    2. 사용자 메시지 DB 저장
    3. AI 스트리밍 응답 생성
    4. AI 응답 완료 후 DB 저장
    """
    stream_start_time = time.time()

    try:
        # Step 1: 세션 확인/생성
        if not request.session_id:
            from services.chat.session_manager import ChatSessionCreate
            session = await session_manager.create_session(ChatSessionCreate(
                user_id=request.user_id,
                chat_service_type=request.chat_service_type,
                llm_provider=request.provider,
                llm_model=request.model
            ))
            session_id = session.id
            logger.info(f"New session created: {session_id}")
        else:
            session_id = request.session_id
            # 세션 존재 확인
            existing_session = await session_manager.get_session(session_id)
            if not existing_session:
                raise HTTPException(404, f"Session not found: {session_id}")

        # Step 2: 사용자 메시지 저장
        user_message_saved = await session_manager.save_message(ChatMessageCreate(
            session_id=session_id,
            role="user",
            content=request.message
        ))
        logger.info(f"User message saved: {user_message_saved.id}")

        # Step 3: 직접 스트리밍 방식으로 채팅 처리 (Redis 제거)
        from core.llm.types import LLMProvider
        from services.chat.types import ChatServiceEnum

        chat_req = ChatRequest(
            message=request.message,
            provider=LLMProvider(request.provider),
            model=request.model,
            max_tokens=request.max_tokens,
            chat_service_type=ChatServiceEnum(request.chat_service_type)
        )

        # Chat service 생성
        service_class = get_chat(chat_req.chat_service_type)
        chat_service = service_class(provider=chat_req.provider, model_name=chat_req.model)
        logger.info(f"Chat service created for session: {session_id}")

        # Step 4: 스트리밍 응답 생성
        async def generate():
            stream_completed = False
            chunks_sent = 0
            full_response = ""
            ai_message_id = None

            try:
                # 세션 ID를 첫 청크로 전송
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

                async for stream_data in chat_service.chat_stream(chat_req):
                    try:
                        # SSE 형식으로 데이터 전송
                        sse_data = f"data: {json.dumps(stream_data)}\n\n"
                        yield sse_data

                        # 응답 수집
                        if stream_data.get('type') == 'chunk':
                            chunks_sent += 1
                            full_response = stream_data.get('full_response', full_response)

                        # 완료 신호
                        if stream_data.get('type') == 'complete':
                            stream_completed = True
                            full_response = stream_data.get('full_response', full_response)

                            # AI 응답 DB 저장
                            tools_used = stream_data.get('tools_used', {})
                            visualization_data = stream_data.get('visualization')
                            processing_time_ms = int((time.time() - stream_start_time) * 1000)

                            ai_message = await session_manager.save_message(ChatMessageCreate(
                                session_id=session_id,
                                role="assistant",
                                content=full_response,
                                model_used=request.model,
                                tools_used=tools_used if tools_used else None,
                                processing_time_ms=processing_time_ms,
                                visualization=visualization_data
                            ))
                            ai_message_id = ai_message.id

                            logger.info(f"AI message saved: {ai_message_id}")
                            break

                        elif stream_data.get('type') == 'error':
                            logger.error(f"Stream error: {stream_data.get('error')}")
                            break

                    except Exception as sse_send_error:
                        logger.error(f"SSE send error: {sse_send_error}")
                        continue

                # 완료 통계
                if stream_completed:
                    elapsed_time = time.time() - stream_start_time
                    logger.info(
                        f"Stream completed: session={session_id}, "
                        f"chunks={chunks_sent}, time={elapsed_time:.2f}s"
                    )

            except Exception as gen_error:
                logger.error(f"Generate error: {gen_error}")
                error_data = {
                    'type': 'error',
                    'error': str(gen_error),
                    'session_id': session_id
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"❌ Chat stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# 대화 재개 API
# =====================================================
@router.post("/chat/continue/{session_id}")
async def continue_chat(
    session_id: str,
    message: str,
    user_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    기존 대화 이어가기

    세션 ID로 대화 히스토리를 불러와서 계속 대화
    """
    # 세션 존재 확인
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # 기존 메시지 불러오기
    history = await session_manager.get_messages_as_langchain(session_id, limit=10)
    logger.info(f"Loaded {len(history)} messages from session: {session_id}")

    # 새 요청 생성
    request = ChatRequestWithSession(
        message=message,
        session_id=session_id,
        user_id=user_id,
        chat_service_type=session.chat_service_type,
        provider=session.llm_provider or "anthropic",
        model=session.llm_model or "claude-sonnet-4-6"
    )

    return await chat_stream_with_history(request, session_manager)


# =====================================================
# Health Check
# =====================================================
@router.get("/chat/integrated/health")
async def integrated_chat_health():
    """통합 채팅 시스템 상태"""
    return {
        "status": "healthy",
        "features": [
            "Session management",
            "Message persistence",
            "Streaming responses",
            "Chat history"
        ]
    }
