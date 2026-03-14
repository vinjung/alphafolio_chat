from models import ChatRequest, ChatResponse
from config import logger
from datetime import date, datetime
from typing import AsyncGenerator, Dict, Any, List
from services.chat.base import BaseChatService, ChatServiceEnum
from services.chat_history_service import ChatHistoryService
from services.cache_manager import CacheManager, MarketType
from database import db
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from .graph import braincrash_graph
from .graph.types import BrainCrashGraphState


class BrainCrashChatService(BaseChatService):  # 뇌절 AI
    chat_type = ChatServiceEnum.BRAIN_CRASH

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 히스토리 서비스 초기화
        self.history_service = ChatHistoryService(db.pool) if db.pool else None
        # 캐시 매니저 초기화 (Redis removed)
        self.cache_manager = None

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        # ToDo Define Checkpointer
        ai_message: AIMessage = AIMessage(content="죄송합니다. 응답을 생성할 수 없습니다.")
        state: BrainCrashGraphState = self.graph_state | {"user_query": request.message, "provider": request.get_provider(), "model": request.get_model()}
        try:
            terminal_state: BrainCrashGraphState = await braincrash_graph.ainvoke(state)
        except Exception as e:
            logger.error(f"[BrainCrashChatService] Chat service error: {str(e)}")
        else:
            for msg in reversed(terminal_state['messages']):
                if isinstance(msg, AIMessage):
                    ai_message = msg
                    if isinstance(ai_message.content, list):
                        ai_message.content = ai_message.content[0]
                    if isinstance(ai_message.content, dict):
                        ai_message.content = ai_message.content.get("text")
                    break
        return ChatResponse(
            response=ai_message.content,
            usage={},
            model=request.get_model()
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """SSE 스트리밍 방식 (히스토리 지원)"""

        # 1. 세션 관리
        session_id = getattr(request, 'sessionId', None) or getattr(request, 'session_id', None)
        if not session_id and self.history_service:
            # 새 세션 생성
            session_id = await self.history_service.create_session(
                user_id=getattr(request, 'user_id', None),
                chat_service_type="BRAIN_CRASH",
                llm_provider=request.get_provider().value,
                llm_model=request.get_model()
            )
            logger.info(f"[BrainCrash] New session created: {session_id}")

        # 2. 대화 히스토리 로드
        history_messages = []
        if session_id and self.history_service:
            try:
                history_messages = await self.history_service.convert_messages_to_langchain_format(
                    session_id,
                    limit=20  # 최근 20개 메시지
                )
                logger.info(f"[BrainCrash] Loaded {len(history_messages)} history messages")
            except Exception as e:
                logger.warning(f"[BrainCrash] Failed to load history: {e}")

        # 3. 사용자 메시지 저장
        if session_id and self.history_service:
            try:
                await self.history_service.add_message(
                    session_id=session_id,
                    role="user",
                    content=request.message
                )
            except Exception as e:
                logger.error(f"[BrainCrash] Failed to save user message: {e}")

        # 3a. 캐시 체크 (LLM 응답 캐싱)
        cache_key = f"{request.message}_{request.get_model()}"
        if self.cache_manager:
            cached_response = await self.cache_manager.get(MarketType.GENERAL, cache_key)
            if cached_response:
                logger.info(f"[BrainCrash] Cache hit for: {request.message[:50]}...")
                # 캐시된 응답을 스트리밍 형식으로 반환
                content = cached_response.get('content', '')
                yield {
                    "type": "chunk",
                    "content": content,
                    "full_response": content
                }
                yield {
                    "type": "complete",
                    "content": "",
                    "full_response": content,
                    "model": request.get_model(),
                    "session_id": session_id,
                    "tools_used": cached_response.get('tools_used', {}),
                    "usage": cached_response.get('usage', {}),
                    "finish_reason": "cached",
                    "completion_status": "cached",
                    "is_truly_complete": True
                }
                return

        # 4. 히스토리를 state에 포함
        state: BrainCrashGraphState = self.graph_state | {
            "user_query": request.message,
            "messages": self._convert_history_to_langchain(history_messages)
        }

        # 시작 시간 기록
        pipeline_start = datetime.now()

        try:
            stream = braincrash_graph.astream_events(state)

            full_response = ""
            tool_ids = {None}
            chunk_count = 0
            last_chunk_content = ""

            # 진단용 변수
            last_event_type = None
            last_few_events = []
            stream_ended_naturally = False
            had_error = False
            total_events = 0

            # Usage 정보
            usage_metadata = None
            finish_reason = None

            # Tool 사용 카운터
            tools_used = {}

            logger.info(f"[BrainCrash] Starting stream for: {request.message[:50]}...")

            async for event in stream:
                total_events += 1
                event_type = event.get("event", None)

                # 진단용: 마지막 10개 이벤트 타입 추적
                last_few_events.append(event_type)
                if len(last_few_events) > 10:
                    last_few_events.pop(0)
                last_event_type = event_type

                if event_type in {"on_chain_start", "on_chat_model_start"}:
                    continue
                elif event_type in {"on_chain_end", "on_chat_model_end"}:
                    stream_ended_naturally = True

                    # Usage 메타데이터 추출
                    if event_type == "on_chat_model_end":
                        data = event.get("data", {})
                        output = data.get("output", {})

                        if hasattr(output, 'usage_metadata'):
                            usage_metadata = output.usage_metadata
                            logger.info(f"[BrainCrash] Usage metadata: {usage_metadata}")

                        if hasattr(output, 'response_metadata'):
                            response_meta = output.response_metadata
                            finish_reason = response_meta.get('stop_reason') or response_meta.get('finish_reason')
                            logger.info(f"[BrainCrash] Finish reason: {finish_reason}")

                    continue
                elif event_type in {"on_chain_error", "on_chat_model_error", "on_tool_error"}:
                    had_error = True
                    error_data = event.get("data", {})
                    error_msg = error_data.get("error") or str(error_data)
                    logger.error(f"[BrainCrash] Error event detected: {event_type} - {error_msg}")
                    continue
                elif event_type == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk is not None and isinstance(chunk, AIMessage):
                        chunk_count += 1

                        if chunk.tool_calls:
                            for tc in chunk.tool_calls:
                                tool_id = tc.get("id")
                                tool_name = tc.get("name", "Unknown")

                                if tool_id not in tool_ids:
                                    tool_ids.add(tool_id)

                                    # Tool 사용 카운트
                                    if tool_name not in tools_used:
                                        tools_used[tool_name] = 0
                                    tools_used[tool_name] += 1

                            if len(tool_ids) == 1:
                                content = "\n더 정확한 정보를 위해 웹에서 정보를 수집중입니다. 잠시만 기다려주세요.\n"
                                full_response += content
                                yield {
                                    "type": "chunk",
                                    "content": content,
                                    "full_response": full_response
                                }
                        elif chunk.content:
                            for cont in chunk.content:
                                if cont.get("type") == "text":
                                    txt = cont.get("text", "")
                                    full_response += txt
                                    last_chunk_content = txt

                                    yield {
                                        "type": "chunk",
                                        "content": txt,
                                        "full_response": full_response
                                    }
                        else:
                            pass
                else:
                    pass

            # 스트림 종료 진단
            response_length = len(full_response)

            # Tool 사용 통계 로깅
            tools_summary = ", ".join([f"{k}:{v}" for k, v in tools_used.items() if v > 0])
            logger.info(f"[BrainCrash] Tools used: {tools_summary or 'None'}")

            # 이중 검증: finish_reason (우선) + event (보조)
            is_truly_complete = False
            completion_status = "unknown"

            if finish_reason:
                if finish_reason in ['end_turn', 'stop', 'stop_sequence']:
                    is_truly_complete = True
                    completion_status = "normal"

                    if not stream_ended_naturally:
                        logger.warning(f"[BrainCrash] Signal conflict: finish_reason='{finish_reason}' but no end event")
                        completion_status = "normal_with_event_mismatch"

                    if had_error:
                        logger.warning(f"[BrainCrash] finish_reason='{finish_reason}' but error event occurred")
                        completion_status = "normal_with_error_event"

                elif finish_reason == 'max_tokens':
                    is_truly_complete = False
                    completion_status = "truncated_max_tokens"
                    logger.warning(f"[BrainCrash] Response truncated: max_tokens reached!")

                elif finish_reason == 'length':
                    is_truly_complete = False
                    completion_status = "truncated_length"
                    logger.warning(f"[BrainCrash] Response truncated: length limit!")

                else:
                    completion_status = f"other_{finish_reason}"
                    logger.warning(f"[BrainCrash] Unknown finish_reason: {finish_reason}")

            else:
                if had_error:
                    is_truly_complete = False
                    completion_status = "error_occurred"
                    logger.error(f"[BrainCrash] Stream ended with error event")

                elif stream_ended_naturally:
                    is_truly_complete = True
                    completion_status = "complete_via_event_only"
                    logger.warning(f"[BrainCrash] No finish_reason, relying on end event")

                else:
                    is_truly_complete = False
                    completion_status = "incomplete_no_signals"
                    logger.error(f"[BrainCrash] No finish_reason AND no end event!")
                    logger.error(f"[BrainCrash] Last event: {last_event_type}")
                    logger.error(f"[BrainCrash] Last 10 events: {last_few_events}")
                    logger.error(f"[BrainCrash] Total events: {total_events}, Chunks: {chunk_count}")

                    if full_response and not full_response.rstrip().endswith(('.', '!', '?', '요', '다', '\n', ')', ']', '}')):
                        logger.warning(f"[BrainCrash] Response appears truncated (heuristic)!")
                        logger.warning(f"[BrainCrash] Last 200 chars: ...{full_response[-200:]}")

            # 최종 완료 로그
            logger.info(
                f"[BrainCrash] Completed: {chunk_count} chunks, {response_length} chars, "
                f"finish_reason={finish_reason}, status={completion_status}, tools={tools_summary}"
            )

            # AI 응답 저장 (히스토리)
            if session_id and self.history_service and full_response:
                try:
                    total_tokens = usage_metadata.get('total_tokens') if usage_metadata else None
                    processing_time_ms = int((datetime.now() - pipeline_start).total_seconds() * 1000)

                    await self.history_service.add_message(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                        tokens_used=total_tokens,
                        model_used=request.get_model(),
                        tools_used=tools_used,
                        processing_time_ms=processing_time_ms
                    )
                    logger.info(f"[BrainCrash] Assistant response saved to history")
                except Exception as e:
                    logger.error(f"[BrainCrash] Failed to save assistant message: {e}")

            # AI 응답을 캐시에 저장
            if self.cache_manager and full_response:
                try:
                    await self.cache_manager.set(
                        MarketType.GENERAL,
                        cache_key,
                        {
                            "content": full_response,
                            "model": request.get_model(),
                            "tools_used": tools_used,
                            "usage": dict(usage_metadata) if usage_metadata else {}
                        }
                    )
                    logger.info(f"[BrainCrash] Response cached successfully")
                except Exception as e:
                    logger.error(f"[BrainCrash] Failed to cache response: {e}")

            # Usage 정보 포함하여 완료 신호 전송
            yield {
                "type": "complete",
                "content": "",
                "full_response": full_response,
                "model": request.get_model(),
                "session_id": session_id,
                "tools_used": tools_used,
                "usage": dict(usage_metadata) if usage_metadata else {},
                "finish_reason": finish_reason,
                "completion_status": completion_status,
                "is_truly_complete": is_truly_complete
            }
        except Exception as e:
            logger.error(f"[BrainCrash] Stream error: {str(e)}")
            logger.error(f"[BrainCrash] Error type: {type(e).__name__}")

            # 예외 발생 시 현재 상태 로깅
            if 'full_response' in locals():
                logger.error(f"[BrainCrash] Partial response length: {len(full_response)}")
                if full_response:
                    logger.error(f"[BrainCrash] Last 100 chars: ...{full_response[-100:]}")

            yield {
                "type": "error",
                "content": "",
                "error": str(e)
            }

    def _convert_history_to_langchain(self, history_messages: List[Dict]) -> List:
        """
        히스토리 메시지를 LangChain 메시지 객체로 변환

        Args:
            history_messages: [{"role": "user", "content": "..."}, ...]

        Returns:
            [HumanMessage(...), AIMessage(...), ...]
        """
        langchain_messages = []

        for msg in history_messages:
            role = msg.get('role')
            content = msg.get('content', '')

            if role == 'user':
                langchain_messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                langchain_messages.append(AIMessage(content=content))
            elif role == 'system':
                langchain_messages.append(SystemMessage(content=content))

        return langchain_messages
