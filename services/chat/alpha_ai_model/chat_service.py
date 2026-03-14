# services/chat/alpha_ai_model/chat_service.py
"""
AlphaAIChatService - Text-to-SQL specialized financial LLM service
"""
import asyncio
from models import ChatRequest, ChatResponse
from config import logger, cache_redis
from typing import AsyncGenerator, Dict, Any, List
from services.chat.base import BaseChatService, ChatServiceEnum
from services.chat_history_service import ChatHistoryService
from services.cache_manager import get_cache_manager, MarketType
from services.queue_manager import request_queue, QueueFullError
from database import db

from .graph.types import AlphaAIGraphState
from .graph.builder import alpha_ai_graph
from .stock_resolver import StockResolver
from langchain_core.messages import AIMessage, HumanMessage


class AlphaAIChatService(BaseChatService):
    """
    Alpha AI - Text-to-SQL specialized financial LLM

    Workflow:
    1. Intent Classification
    2. Entity Extraction
    3. Schema RAG
    4. SQL Generation
    5. SQL Validation & Execution
    6. Response Generation
    """
    chat_type = ChatServiceEnum.ALPHA_AI

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # RAG components (Phase 3)
        self.schema_rag = None
        self.term_mapper = None
        self.vector_store = None
        # Stock resolver
        self._stock_resolver_initialized = False
        # Chat history service for conversation context
        self.history_service = ChatHistoryService(db.pool) if db.pool else None
        # Cache manager (uses Redis for market-aware caching)
        self.cache_manager = get_cache_manager(cache_redis)

    async def _ensure_stock_resolver_initialized(self) -> None:
        """Ensure StockResolver is initialized (lazy initialization)"""
        if not self._stock_resolver_initialized:
            try:
                resolver = StockResolver.get_instance()
                await resolver.initialize()
                self._stock_resolver_initialized = True
                logger.info("[AlphaAI] StockResolver initialized")
            except Exception as e:
                logger.warning(f"[AlphaAI] StockResolver initialization failed: {e}")

    async def _load_conversation_history(
        self,
        session_id: str,
        limit: int = 6
    ) -> List[Dict[str, str]]:
        """
        Load recent conversation history from session

        Args:
            session_id: Session ID to load history from
            limit: Maximum number of messages to load (default: 6 = 3 turns)

        Returns:
            List of messages in format [{"role": "user/assistant", "content": "..."}]
        """
        if not self.history_service or not session_id:
            return []

        try:
            messages = await self.history_service.convert_messages_to_langchain_format(
                session_id=session_id,
                limit=limit
            )
            if messages:
                logger.info(f"[AlphaAI] Loaded {len(messages)} messages from session {session_id[:8]}...")
            return messages
        except Exception as e:
            logger.warning(f"[AlphaAI] Failed to load conversation history: {e}")
            return []

    def _build_initial_state(
        self,
        request: ChatRequest,
        conversation_history: List[Dict[str, str]] = None
    ) -> AlphaAIGraphState:
        """
        Build initial graph state from chat request

        Args:
            request: ChatRequest object
            conversation_history: Previous messages from session

        Returns:
            AlphaAIGraphState initial state
        """
        # Convert conversation history to LangChain message format
        messages = []
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg.get("content", "")))

        return {
            # Input
            "message": request.message,
            "user_id": getattr(request, 'user_id', None),
            "session_id": getattr(request, 'sessionId', None) or getattr(request, 'session_id', None),

            # LLM Configuration
            "provider": request.get_provider(),
            "model_name": request.get_model(),
            "model_config": {},

            # Message History (loaded from session)
            "messages": messages,

            # Initialize empty fields (will be populated by nodes)
            "intent": None,
            "market": None,
            "entities": None,
            "relevant_tables": None,
            "relevant_columns": None,
            "few_shot_examples": None,
            "generated_sql": None,
            "sql_valid": None,
            "sql_error": None,
            "sql_retry_count": 0,
            "query_result": None,
            "result_count": None,
            "execution_time_ms": None,
            "response": None,
            "response_type": None,
            "visualization": None,
            "supplementary_charts": None,
            "processing_steps": [],
            "total_tokens_used": 0
        }

    def _detect_market_type(self, message: str) -> MarketType:
        """Detect market type from message for cache TTL optimization"""
        msg_lower = message.lower()
        us_keywords = ['nasdaq', 'nyse', 's&p', 'vix', 'tesla', 'apple', 'nvidia',
                       'microsoft', 'amazon', 'google', 'meta', 'dollar', 'fed']
        kr_keywords = ['kospi', 'kosdaq', '삼성', '현대', 'sk', 'lg', '네이버',
                       '카카오', '외국인', '기관', '코스피', '코스닥']

        has_us = any(kw in msg_lower for kw in us_keywords)
        has_kr = any(kw in msg_lower for kw in kr_keywords)

        if has_us and not has_kr:
            return MarketType.US
        return MarketType.KR

    async def ainvoke(self, request: ChatRequest) -> ChatResponse:
        """
        Non-streaming chat response using LangGraph workflow

        Args:
            request: ChatRequest with message and configuration

        Returns:
            ChatResponse with generated response

        Raises:
            QueueFullError: If the request queue is full (caught by router -> 503)
        """
        logger.info(f"[AlphaAI] Processing request: {request.message[:50]}...")

        async with request_queue.throttle():
            try:
                # Ensure StockResolver is initialized
                await self._ensure_stock_resolver_initialized()

                # Load conversation history for context
                session_id = getattr(request, 'sessionId', None) or getattr(request, 'session_id', None)
                conversation_history = await self._load_conversation_history(session_id) if session_id else []

                # Build initial state with conversation history
                initial_state = self._build_initial_state(request, conversation_history)

                # Cache check
                cache_key = f"alpha_ai:{request.message}:{request.get_model()}"
                market_type = self._detect_market_type(request.message)
                if self.cache_manager:
                    cached = await self.cache_manager.get(market_type, cache_key)
                    if cached:
                        logger.info(f"[AlphaAI] Cache hit (ainvoke): {request.message[:50]}...")
                        return ChatResponse(
                            response=cached.get('content', ''),
                            usage=cached.get('usage', {}),
                            model=request.get_model(),
                            metadata=cached.get('metadata', {})
                        )

                # Run the graph
                final_state = await alpha_ai_graph.ainvoke(initial_state)

                # Extract response
                response_content = final_state.get("response", "No response generated")

                # Build metadata
                supplementary_charts_data = final_state.get("supplementary_charts")
                metadata = {
                    "intent": final_state.get("intent"),
                    "market": final_state.get("market"),
                    "sql": final_state.get("generated_sql"),
                    "sql_valid": final_state.get("sql_valid"),
                    "result_count": final_state.get("result_count"),
                    "execution_time_ms": final_state.get("execution_time_ms"),
                    "processing_steps": final_state.get("processing_steps", []),
                    "visualization": final_state.get("visualization"),
                    "supplementary_charts": supplementary_charts_data
                }

                logger.info(f"[AlphaAI] Response generated: {len(response_content)} chars")
                if final_state.get("visualization"):
                    logger.info(f"[AlphaAI] Visualization: {final_state['visualization'].get('type')}")
                if supplementary_charts_data:
                    chart_count = len(supplementary_charts_data.get('data', {}).get('charts', []))
                    logger.info(f"[AlphaAI] Supplementary charts: {chart_count} tabs")
                logger.debug(f"[AlphaAI] Metadata: {metadata}")

                # Cache save
                if self.cache_manager and response_content:
                    try:
                        cache_data = {
                            'content': response_content,
                            'usage': {"total_tokens": final_state.get("total_tokens_used", 0)},
                            'metadata': metadata,
                            'supplementary_charts': supplementary_charts_data
                        }
                        await self.cache_manager.set(market_type, cache_key, cache_data)
                    except Exception as e:
                        logger.warning(f"[AlphaAI] Cache save failed: {e}")

                return ChatResponse(
                    response=response_content,
                    usage={"total_tokens": final_state.get("total_tokens_used", 0)},
                    model=request.get_model(),
                    metadata=metadata
                )

            except Exception as e:
                logger.error(f"[AlphaAI] Error processing request: {str(e)}")
                return ChatResponse(
                    response=f"Error processing request: {str(e)}",
                    usage={},
                    model=request.get_model()
                )

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """
        SSE streaming chat response using LangGraph workflow with real-time streaming

        Uses astream_events to stream LLM tokens as they are generated.
        Wrapped with request_queue.throttle() to limit concurrent pipeline executions.
        QueueFullError is caught and sent as an SSE error event.

        Args:
            request: ChatRequest with message and configuration

        Yields:
            Dict with streaming response chunks
        """
        logger.info(f"[AlphaAI] Starting stream for: {request.message[:50]}...")

        async with request_queue.throttle():
            try:
                # Ensure StockResolver is initialized
                await self._ensure_stock_resolver_initialized()

                # Load conversation history for context
                session_id = getattr(request, 'sessionId', None) or getattr(request, 'session_id', None)
                conversation_history = await self._load_conversation_history(session_id) if session_id else []

                # Build initial state with conversation history
                initial_state = self._build_initial_state(request, conversation_history)

                # Cache check
                cache_key = f"alpha_ai:{request.message}:{request.get_model()}"
                market_type = self._detect_market_type(request.message)
                if self.cache_manager:
                    cached = await self.cache_manager.get(market_type, cache_key)
                    if cached:
                        logger.info(f"[AlphaAI] Cache hit (stream): {request.message[:50]}...")
                        content = cached.get('content', '')
                        yield {
                            "type": "chunk",
                            "content": content,
                            "full_response": content
                        }
                        yield {
                            "type": "complete",
                            "finish_reason": "stop",
                            "is_truly_complete": True,
                            "completion_status": "cached",
                            "full_response": content,
                            "metadata": cached.get('metadata', {}),
                            "visualization": cached.get('visualization'),
                            "supplementary_charts": cached.get('supplementary_charts')
                        }
                        return

                # Send processing status
                yield {
                    "type": "status",
                    "content": "Processing query...",
                    "status": "processing"
                }

                # Tracking variables
                full_response = ""
                chunk_count = 0
                current_node = ""
                generated_sql = ""
                sql_valid = False
                sql_error = None
                finish_reason = None
                stream_ended_naturally = False
                had_error = False
                final_state = {}

                # Stream events from the graph
                stream = alpha_ai_graph.astream_events(initial_state, version="v2")

                async for event in stream:
                    event_type = event.get("event")

                    # Track node transitions for status updates
                    if event_type == "on_chain_start":
                        name = event.get("name", "")
                        if name and name != current_node:
                            current_node = name
                            # Send status update for major processing steps
                            if name in ["intent_classifier", "entity_extractor", "unified_classifier",
                                        "query_router", "query_decomposer", "parallel_sql_pipeline",
                                        "schema_retriever", "sql_generator", "sql_validator",
                                        "sql_executor", "context_enricher", "response_generator"]:
                                status_map = {
                                    "intent_classifier": "Analyzing intent...",
                                    "entity_extractor": "Extracting entities...",
                                    "unified_classifier": "Analyzing query...",
                                    "query_router": "Analyzing query...",
                                    "query_decomposer": "Decomposing query...",
                                    "parallel_sql_pipeline": "Executing SQL queries...",
                                    "schema_retriever": "Retrieving schema...",
                                    "sql_generator": "Generating SQL...",
                                    "sql_validator": "Validating SQL...",
                                    "sql_executor": "Executing query...",
                                    "context_enricher": "Enriching context...",
                                    "response_generator": "Generating response..."
                                }
                                yield {
                                    "type": "status",
                                    "content": status_map.get(name, f"Processing {name}..."),
                                    "status": "processing",
                                    "node": name
                                }

                    elif event_type == "on_chain_end":
                        stream_ended_naturally = True
                        # Capture final state data
                        data = event.get("data", {})
                        output = data.get("output", {})
                        if isinstance(output, dict):
                            if output.get("generated_sql"):
                                generated_sql = output.get("generated_sql", "")
                                sql_valid = output.get("sql_valid", False)
                                sql_error = output.get("sql_error")
                                # Send SQL info
                                if generated_sql:
                                    yield {
                                        "type": "sql",
                                        "content": generated_sql,
                                        "sql_valid": sql_valid,
                                        "sql_error": sql_error
                                    }
                            # Capture final state for metadata
                            for key in ["intent", "market", "result_count", "execution_time_ms", "processing_steps", "visualization", "supplementary_charts", "response"]:
                                if key in output:
                                    # Don't overwrite visualization with None from intermediate nodes
                                    if key == "visualization" and output[key] is None and final_state.get(key) is not None:
                                        continue
                                    final_state[key] = output[key]

                    elif event_type == "on_chat_model_end":
                        # Extract finish reason from main LLM (Anthropic only)
                        # Ignore OpenAI auxiliary calls (e.g., GPT-4o-mini news summary)
                        # to prevent overwriting the main response LLM's completion status
                        data = event.get("data", {})
                        output = data.get("output", {})
                        if hasattr(output, 'response_metadata'):
                            response_meta = output.response_metadata
                            _stop = response_meta.get('stop_reason')
                            if _stop:
                                finish_reason = _stop

                    elif event_type in {"on_chain_error", "on_chat_model_error"}:
                        had_error = True
                        error_data = event.get("data", {})
                        error_msg = str(error_data.get("error", error_data))
                        logger.error(f"[AlphaAI] Error event: {event_type} - {error_msg}")

                    elif event_type == "on_chat_model_stream":
                        # Real-time token streaming - only from response_generator node
                        chunk = event.get("data", {}).get("chunk")
                        if chunk is not None and isinstance(chunk, AIMessage):
                            if chunk.content:
                                chunk_count += 1
                                # Handle content that can be string or list
                                content_text = ""
                                if isinstance(chunk.content, str):
                                    content_text = chunk.content
                                elif isinstance(chunk.content, list):
                                    for item in chunk.content:
                                        if isinstance(item, dict) and item.get("type") == "text":
                                            content_text += item.get("text", "")
                                        elif isinstance(item, str):
                                            content_text += item

                                if content_text:
                                    # Only stream output from response_generator node
                                    if current_node == "response_generator":
                                        full_response += content_text
                                        yield {
                                            "type": "chunk",
                                            "content": content_text,
                                            "full_response": full_response
                                        }

                # Simulate streaming for non-LLM responses (e.g., hybrid passthrough)
                if not full_response and final_state.get("response"):
                    full_response = final_state["response"]
                    chunk_size = 8
                    for i in range(0, len(full_response), chunk_size):
                        text_chunk = full_response[i:i + chunk_size]
                        yield {
                            "type": "chunk",
                            "content": text_chunk,
                            "full_response": full_response[:i + chunk_size],
                        }
                        await asyncio.sleep(0.01)
                    logger.info(
                        f"[AlphaAI] Simulated streaming for non-LLM response: "
                        f"{len(full_response)} chars"
                    )

                # Determine completion status
                is_truly_complete = False
                completion_status = "unknown"

                if finish_reason:
                    if finish_reason in ['end_turn', 'stop', 'stop_sequence']:
                        is_truly_complete = True
                        completion_status = "normal"
                    elif finish_reason == 'max_tokens':
                        is_truly_complete = False
                        completion_status = "truncated_max_tokens"
                        logger.warning("[AlphaAI] Response truncated: max_tokens reached")
                    else:
                        completion_status = f"other_{finish_reason}"
                elif had_error:
                    is_truly_complete = False
                    completion_status = "error_occurred"
                elif stream_ended_naturally:
                    is_truly_complete = True
                    completion_status = "complete_via_event"

                # Get visualization data
                visualization_data = final_state.get("visualization")
                supplementary_charts_data = final_state.get("supplementary_charts")

                # Build metadata
                metadata = {
                    "intent": final_state.get("intent"),
                    "market": final_state.get("market"),
                    "sql": generated_sql,
                    "sql_valid": sql_valid,
                    "result_count": final_state.get("result_count"),
                    "execution_time_ms": final_state.get("execution_time_ms"),
                    "processing_steps": final_state.get("processing_steps", []),
                    "visualization": visualization_data,
                    "supplementary_charts": supplementary_charts_data
                }

                logger.info(f"[AlphaAI] Stream completed: {chunk_count} chunks, {len(full_response)} chars, status={completion_status}")
                if supplementary_charts_data:
                    sc_count = len(supplementary_charts_data.get('data', {}).get('charts', []))
                    logger.info(f"[AlphaAI] Supplementary charts: {sc_count} tabs")
                if visualization_data:
                    viz_type = visualization_data.get('type', 'unknown')
                    viz_data = visualization_data.get('data', {})
                    if viz_type == 'table':
                        count = len(viz_data.get('rows', []))
                        logger.info(f"[AlphaAI] Visualization: {viz_type}, {count} rows")
                    elif viz_type == 'multi_chart':
                        chart_count = len(visualization_data.get('data', {}).get('charts', []))
                        logger.info(f"[AlphaAI] Visualization: {viz_type}, {chart_count} charts")
                    else:
                        count = len(viz_data.get('labels', []))
                        logger.info(f"[AlphaAI] Visualization: {viz_type}, {count} data points")

                # Cache save (only for complete responses)
                if self.cache_manager and is_truly_complete and full_response:
                    try:
                        cache_data = {
                            'content': final_state.get("response", full_response),
                            'metadata': metadata,
                            'visualization': visualization_data,
                            'supplementary_charts': supplementary_charts_data
                        }
                        await self.cache_manager.set(market_type, cache_key, cache_data)
                    except Exception as e:
                        logger.warning(f"[AlphaAI] Cache save failed: {e}")

                # Send completion signal
                yield {
                    "type": "complete",
                    "finish_reason": finish_reason or "stop",
                    "is_truly_complete": is_truly_complete,
                    "completion_status": completion_status,
                    "full_response": final_state.get("response", full_response),
                    "metadata": metadata,
                    "visualization": visualization_data,
                    "supplementary_charts": supplementary_charts_data
                }

            except Exception as e:
                logger.error(f"[AlphaAI] Stream error: {str(e)}")
                yield {
                    "type": "error",
                    "content": "",
                    "error": str(e)
                }
