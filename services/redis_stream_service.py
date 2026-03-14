# api/app/services/redis_stream_service.py
import redis
import json
import time
import uuid
from typing import Dict, Any, AsyncGenerator
from models import ChatRequest
from services.chat.factory import get_chat
from config import settings, logger

class RedisStreamService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        self.stream_name = "chat_stream"

    def add_chat_request(self, request: ChatRequest) -> str:
        """채팅 요청을 Redis Stream에 추가"""
        try:
            stream_id = str(uuid.uuid4())

            message_data = {
                'stream_id': stream_id,
                'request_data': request.model_dump_json(),
                'timestamp': str(int(time.time())),
                'status': 'pending'
            }

            self.redis_client.xadd(self.stream_name, message_data)
            logger.info(f"✅ Chat request added to stream: {stream_id}")
            return stream_id

        except Exception as e:
            logger.error(f"❌ Failed to add chat request to stream: {e}")
            raise

    async def process_stream_messages(self, stream_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        특정 stream_id의 메시지를 처리하고 실시간 결과 반환
        """
        consumer_name = f"consumer_{stream_id}"

        try:
            # 해당 stream_id의 메시지 찾기
            message_data = None
            messages = self.redis_client.xread({self.stream_name: '0'})

            for stream, msgs in messages:
                for msg_id, fields in msgs:
                    if fields.get('stream_id', '') == stream_id:
                        message_data = fields
                        break

            if not message_data:
                logger.error(f"❌ Message not found for stream_id: {stream_id}")
                yield {"type": "error", "error": "메시지를 찾을 수 없습니다", "stream_id": stream_id}
                return

            # 요청 데이터 파싱 (Pydantic model_validate_json 사용)
            try:
                request_json = message_data['request_data']
                request = ChatRequest.model_validate_json(request_json)  # ✅ enum 자동 복원
                logger.info(f"🚀 Processing stream message: {stream_id}")
            except Exception as parse_error:
                logger.error(f"❌ Failed to parse request data for {stream_id}: {parse_error}")
                yield {"type": "error", "error": f"요청 데이터 파싱 실패: {str(parse_error)}", "stream_id": stream_id}
                return

            # 시작 알림
            yield {
                "type": "start",
                "message": "스트리밍을 시작합니다...",
                "stream_id": stream_id
            }

            # 채팅 서비스 생성
            try:
                service_class = get_chat(request.chat_service_type)
                chat_service = service_class(
                    provider=request.provider,
                    model_name=request.model
                )
                logger.info(f"✅ Chat service created for {stream_id}: {request.chat_service_type.value}")
            except Exception as service_error:
                logger.error(f"❌ Failed to create chat service for {stream_id}: {service_error}")
                yield {"type": "error", "error": f"채팅 서비스 생성 실패: {str(service_error)}", "stream_id": stream_id}
                return

            # 스트리밍 처리
            full_response = ""
            chunk_count = 0
            start_time = time.time()
            last_chunk_content = ""
            total_content_length = 0

            try:
                logger.info(f"🔄 Starting chunk processing for {stream_id}")
                logger.info(f"📝 Request message: {request.message[:100]}...")

                async for chunk in chat_service.chat_stream(request):
                    try:
                        chunk_count += 1

                        # 실제 chat_stream에서 반환되는 딕셔너리 형태 처리
                        if chunk.get('type') == 'chunk' and chunk.get('content'):
                            content = chunk['content']
                            full_response = chunk.get('full_response', full_response + content)
                            last_chunk_content = content
                            total_content_length = len(full_response)

                            yield {
                                "type": "chunk",
                                "content": content,
                                "full_response": full_response,
                                "chunk_numbner": chunk_count  # 오타도 그대로 유지
                            }
                        elif chunk.get('type') == 'complete':
                            # 완료 신호 처리
                            full_response = chunk.get('full_response', full_response)

                            # 응답 완성도 검증 로깅
                            response_length = len(full_response)
                            logger.info(f"✅ Response complete for {stream_id}: {chunk_count} chunks, {response_length} chars")

                            # 응답이 잘렸는지 체크
                            if full_response and not full_response.rstrip().endswith(('.', '!', '?', '요', '다', '\n', ')', ']', '}')):
                                logger.warning(f"⚠️ Response may be truncated for {stream_id}")
                                logger.warning(f"⚠️ Last 200 chars: ...{full_response[-200:]}")
                                logger.warning(f"⚠️ Last chunk: {last_chunk_content}")

                            # 응답 내용 로깅 (너무 길면 일부만)
                            if response_length > 1000:
                                logger.info(f"📄 Response preview (first 300): {full_response[:300]}...")
                                logger.info(f"📄 Response preview (last 300): ...{full_response[-300:]}")
                            else:
                                logger.info(f"📄 Full response: {full_response}")

                            yield chunk  # 완료 신호 그대로 전달
                            break
                        elif chunk.get('type') == 'error':
                            # 에러 신호 처리
                            yield chunk  # 에러 신호 그대로 전달
                            break

                        # 주기적으로 처리 상태 로깅 (매 50개 청크마다)
                        if chunk_count % 50 == 0:
                            logger.info(f"🔄 Processing chunks for {stream_id}: {chunk_count} chunks, {len(full_response)} chars")
                            # 마지막 몇 글자도 로깅하여 진행상황 확인
                            if full_response:
                                logger.info(f"🔄 Current ending: ...{full_response[-50:]}")

                    except Exception as chunk_error:
                        logger.error(f"❌ Error processing chunk {chunk_count} for {stream_id}: {chunk_error}")
                        # 개별 청크 에러는 스트림을 중단하지 않고 계속 진행
                        continue

                # chat_stream에서 이미 완료/에러 신호를 처리하므로 추가 처리 불필요
                final_length = len(full_response)
                logger.info(f"✅ Stream processing ended for {stream_id}: {chunk_count} chunks, {final_length} chars")

                # 스트림이 완료 신호 없이 끝난 경우 추가 로깅
                if final_length > 0 and not full_response.rstrip().endswith(('.', '!', '?', '요', '다', '\n', ')', ']', '}')):
                    logger.warning(f"⚠️ Stream ended without proper completion for {stream_id}")
                    logger.warning(f"⚠️ Final response appears truncated: ...{full_response[-200:]}")

            except Exception as streaming_error:
                # 스트리밍 중 에러 발생
                elapsed_time = time.time() - start_time
                logger.error(f"❌ Streaming error in {stream_id}: {streaming_error}")
                logger.error(f"❌ Error type: {type(streaming_error).__name__}")
                logger.error(f"❌ Processing stats: {chunk_count} chunks, {len(full_response)} chars, {elapsed_time:.2f}s")

                # 상세한 traceback 로깅
                import traceback
                logger.error(f"❌ Streaming traceback for {stream_id}: {traceback.format_exc()}")

                yield {
                    "type": "error",
                    "error": f"스트리밍 처리 중 오류: {str(streaming_error)}",
                    "error_type": type(streaming_error).__name__,
                    "stream_id": stream_id,
                    "partial_response": full_response if full_response else None,
                    "processed_chunks": chunk_count
                }

        except Exception as setup_error:
            # 초기 설정 에러
            logger.error(f"❌ Stream setup error for {stream_id}: {setup_error}")
            logger.error(f"❌ Setup error type: {type(setup_error).__name__}")

            # 상세한 traceback 로깅
            import traceback
            logger.error(f"❌ Setup traceback for {stream_id}: {traceback.format_exc()}")

            yield {
                "type": "error",
                "error": f"스트림 설정 오류: {str(setup_error)}",
                "error_type": type(setup_error).__name__,
                "stream_id": stream_id
            }

    def get_stream_status(self):
        """Redis Stream 상태 조회"""
        try:
            # Redis 연결 확인
            self.redis_client.ping()

            # 스트림 정보 조회
            stream_info = self.redis_client.xinfo_stream(self.stream_name)

            return {
                "redis_connected": True,
                "stream_name": self.stream_name,
                "stream_length": stream_info.get('length', 0),
                "last_generated_id": stream_info.get('last-generated-id', 'N/A'),
                "status": "healthy"
            }
        except redis.ConnectionError:
            logger.error("❌ Redis connection failed")
            return {
                "redis_connected": False,
                "error": "Redis connection failed",
                "status": "unhealthy"
            }
        except Exception as e:
            logger.error(f"❌ Stream status check failed: {e}")
            return {
                "redis_connected": False,
                "error": str(e),
                "status": "unhealthy"
            }

# 싱글톤 인스턴스
redis_stream_service = RedisStreamService()
