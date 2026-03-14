# api/app/routers/chat.py
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from models import ChatRequest, ChatResponse
from services.chat.factory import get_chat
from services.chat.base import BaseChatService
from core.llm.factory import _get_default_model
from core.rate_limiter import limiter
from services.queue_manager import QueueFullError
from config import logger, settings
import json
import time
import asyncio

router = APIRouter()

def get_dynamic_chat_service(chat_request: ChatRequest) -> BaseChatService:
    """Dynamic Chat Service instance creation"""
    try:
        service_type = chat_request.chat_service_type
        service_class = get_chat(service_type)
        return service_class(provider=chat_request.provider, model_name=chat_request.model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid chat service type: {str(e)}")

# Basic test API
@router.post("/", response_model=ChatResponse)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    chat_service: BaseChatService = Depends(get_dynamic_chat_service)
):
    """Basic chat API (test)"""
    if chat_request.model is None:
        chat_request.model = _get_default_model(chat_request.provider)
    try:
        return await chat_service.ainvoke(chat_request)
    except QueueFullError:
        raise HTTPException(status_code=503, detail="Server is busy. Please try again later.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# SSE Streaming API
@router.post("/stream")
@limiter.limit(settings.RATE_LIMIT_STREAM)
async def chat_stream(request: Request, chat_request: ChatRequest):
    """SSE Streaming API (direct streaming)"""
    if chat_request.model is None:
        chat_request.model = _get_default_model(chat_request.provider)
    stream_start_time = time.time()

    try:
        # Development environment: detailed logging
        if settings.railway_environment == "development":
            logger.info(f"Request: {chat_request.message[:50]}... | Provider: {chat_request.provider.value} | Service: {chat_request.chat_service_type.value}")

        # Create chat service
        service_class = get_chat(chat_request.chat_service_type)
        chat_service = service_class(provider=chat_request.provider, model_name=chat_request.model)
        logger.info(f"SSE Stream started for service: {chat_request.chat_service_type.value}")

        # Streaming response
        async def generate():
            stream_completed = False
            error_occurred = False
            chunks_sent = 0
            last_activity_time = time.time()

            try:
                logger.info(f"Starting SSE generation")

                async for stream_data in chat_service.chat_stream(chat_request):
                    try:
                        # Update activity time
                        last_activity_time = time.time()

                        # Send data in SSE format
                        sse_data = f"data: {json.dumps(stream_data)}\n\n"
                        yield sse_data

                        # Increment chunk count
                        if stream_data.get('type') == 'chunk':
                            chunks_sent += 1

                        # Log progress periodically (every 100 chunks)
                        if chunks_sent > 0 and chunks_sent % 100 == 0:
                            elapsed = time.time() - stream_start_time
                            logger.info(f"SSE Progress: {chunks_sent} chunks sent ({elapsed:.1f}s)")

                        # Check for completion or error signals
                        if stream_data.get('type') == 'complete':
                            stream_completed = True
                            elapsed_time = time.time() - stream_start_time
                            logger.info(f"SSE Stream completed: ({elapsed_time:.2f}s, {chunks_sent} chunks)")
                            break
                        elif stream_data.get('type') == 'error':
                            error_occurred = True
                            elapsed_time = time.time() - stream_start_time
                            logger.error(f"SSE Stream error: ({elapsed_time:.2f}s, {chunks_sent} chunks) - {stream_data.get('error', 'Unknown error')}")
                            break

                    except Exception as sse_send_error:
                        logger.error(f"SSE send error: {sse_send_error}")
                        # Individual send errors don't stop the stream
                        continue

                # Detect stream ending without completion signal
                if not stream_completed and not error_occurred:
                    elapsed_time = time.time() - stream_start_time
                    inactive_time = time.time() - last_activity_time

                    logger.error(f"Stream ended without completion signal")
                    logger.error(f"Stream stats: {elapsed_time:.2f}s total, {inactive_time:.2f}s since last activity, {chunks_sent} chunks sent")

                    # Notify client of unexpected end
                    error_data = {
                        'type': 'error',
                        'error': 'Stream ended unexpectedly',
                        'debug_info': {
                            'elapsed_time': elapsed_time,
                            'chunks_sent': chunks_sent,
                            'inactive_time': inactive_time
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

            except asyncio.CancelledError:
                # Client disconnected
                elapsed_time = time.time() - stream_start_time
                logger.info(f"SSE Stream cancelled by client: ({elapsed_time:.2f}s, {chunks_sent} chunks)")
                raise  # Must re-raise CancelledError

            except Exception as gen_error:
                elapsed_time = time.time() - stream_start_time
                logger.error(f"Generate error: {gen_error}")
                logger.error(f"Generate error type: {type(gen_error).__name__}")
                logger.error(f"Generate stats: {elapsed_time:.2f}s, {chunks_sent} chunks sent")

                # Detailed traceback logging
                import traceback
                logger.error(f"Generate traceback: {traceback.format_exc()}")

                # Send error to client
                error_data = {
                    'type': 'error',
                    'error': str(gen_error),
                    'error_type': type(gen_error).__name__
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Accel-Buffering": "no",  # Disable Nginx buffering
            }
        )

    except QueueFullError:
        raise HTTPException(status_code=503, detail="Server is busy. Please try again later.")

    except Exception as e:
        elapsed_time = time.time() - stream_start_time
        logger.error(f"Stream setup error: {e}")
        logger.error(f"Stream setup error type: {type(e).__name__}")
        logger.error(f"Setup failed after {elapsed_time:.2f}s")

        if settings.railway_environment == "development":
            import traceback
            logger.error(f"Setup traceback: {traceback.format_exc()}")

        raise HTTPException(status_code=500, detail=str(e))

# WebSocket and Redis status endpoints removed (Redis no longer used)

@router.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "message": "Chat API is running"
    }
