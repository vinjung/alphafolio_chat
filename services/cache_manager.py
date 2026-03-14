"""
Cache Manager for Stock Data
지능형 캐싱 시스템 - 시장별/시간대별 차등 TTL
"""
import json
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any
from config import logger
from enum import Enum


class MarketType(Enum):
    """시장 구분"""
    US = "US"      # 미국 주식
    KR = "KR"      # 한국 주식
    GENERAL = "GENERAL"  # 일반 데이터


class CacheManager:
    """
    주식 데이터 캐싱 매니저

    캐싱 전략:
    - 미국 주식: 매일 오전 8시 업데이트 기준, 다음날 오전 8시까지 캐싱
    - 한국 주식 (장중): 오전 9:30 ~ 오후 4:00, 30분 TTL
    - 한국 주식 (장마감 후): 오후 4:00 이후, 다음날 오전 9:30까지 캐싱
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client

    def _get_cache_key(self, market: MarketType, query: str) -> str:
        """캐시 키 생성"""
        # 쿼리 정규화 (대소문자, 공백 제거)
        normalized_query = query.lower().strip().replace(" ", "_")
        return f"stock_cache:{market.value}:{normalized_query}"

    def _calculate_kr_stock_ttl(self) -> int:
        """
        한국 주식 TTL 계산
        - 장중 (09:30-16:00): 30분 (1800초)
        - 장마감 후 (16:00-익일 09:30): 다음날 09:30까지
        """
        now = datetime.now()
        current_time = now.time()

        # 장중 시간 (09:30 ~ 16:00)
        market_open = time(9, 30)
        market_close = time(16, 0)

        if market_open <= current_time < market_close:
            # 장중: 30분 TTL
            ttl = 30 * 60  # 1800초
            logger.info(f"[Cache] KR Stock (장중): 30분 캐싱")
        else:
            # 장마감 후: 다음날 09:30까지
            if current_time >= market_close:
                # 오늘 16:00 이후 → 다음날 09:30
                next_open = datetime.combine(
                    now.date() + timedelta(days=1),
                    market_open
                )
            else:
                # 오늘 09:30 이전 → 오늘 09:30
                next_open = datetime.combine(now.date(), market_open)

            ttl = int((next_open - now).total_seconds())
            logger.info(f"[Cache] KR Stock (장마감): {ttl//3600}시간 {(ttl%3600)//60}분 캐싱")

        return ttl

    def _calculate_us_stock_ttl(self) -> int:
        """
        미국 주식 TTL 계산
        - DB 업데이트: 매일 오전 8시
        - 캐싱: 다음날 오전 8시까지
        """
        now = datetime.now()
        update_time = time(8, 0)

        # 다음 업데이트 시간 계산
        if now.time() >= update_time:
            # 오늘 08:00 이후 → 다음날 08:00
            next_update = datetime.combine(
                now.date() + timedelta(days=1),
                update_time
            )
        else:
            # 오늘 08:00 이전 → 오늘 08:00
            next_update = datetime.combine(now.date(), update_time)

        ttl = int((next_update - now).total_seconds())
        logger.info(f"[Cache] US Stock: {ttl//3600}시간 {(ttl%3600)//60}분 캐싱 (다음 업데이트: {next_update})")

        return ttl

    async def get(
        self,
        market: MarketType,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 조회"""
        if not self.redis:
            return None

        cache_key = self._get_cache_key(market, query)

        try:
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                logger.info(f"[Cache] HIT: {cache_key}")
                data = json.loads(cached_data)

                # 캐시 메타정보 추가
                data['_cache_hit'] = True
                data['_cached_at'] = data.get('_cached_at', 'unknown')

                return data
            else:
                logger.info(f"[Cache] MISS: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"[Cache] Get error for {cache_key}: {e}")
            return None

    async def set(
        self,
        market: MarketType,
        query: str,
        data: Dict[str, Any]
    ) -> bool:
        """캐시에 데이터 저장"""
        if not self.redis:
            return False

        cache_key = self._get_cache_key(market, query)

        try:
            # TTL 계산
            if market == MarketType.KR:
                ttl = self._calculate_kr_stock_ttl()
            elif market == MarketType.US:
                ttl = self._calculate_us_stock_ttl()
            else:
                ttl = 300  # 일반 데이터: 5분

            # 캐시 메타정보 추가
            cache_data = {
                **data,
                '_cached_at': datetime.now().isoformat(),
                '_market': market.value,
                '_ttl': ttl
            }

            # Redis에 저장
            await self.redis.setex(
                cache_key,
                ttl,
                json.dumps(cache_data, ensure_ascii=False)
            )

            logger.info(f"[Cache] SET: {cache_key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"[Cache] Set error for {cache_key}: {e}")
            return False

    async def invalidate(self, market: MarketType, query: str) -> bool:
        """캐시 무효화"""
        if not self.redis:
            return False

        cache_key = self._get_cache_key(market, query)

        try:
            result = await self.redis.delete(cache_key)
            logger.info(f"[Cache] INVALIDATE: {cache_key} (deleted: {result})")
            return bool(result)
        except Exception as e:
            logger.error(f"[Cache] Invalidate error for {cache_key}: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        if not self.redis:
            return {
                "total_cached_items": 0,
                "redis_connected": False,
                "error": "Redis client not available"
            }

        try:
            # 전체 캐시 키 개수
            pattern = "stock_cache:*"
            keys = await self.redis.keys(pattern)

            # 시장별 분류
            us_count = len([k for k in keys if ':US:' in k])
            kr_count = len([k for k in keys if ':KR:' in k])
            general_count = len([k for k in keys if ':GENERAL:' in k])

            return {
                "total_cached_items": len(keys),
                "us_stock_cached": us_count,
                "kr_stock_cached": kr_count,
                "general_cached": general_count,
                "redis_connected": True
            }
        except Exception as e:
            logger.error(f"[Cache] Stats error: {e}")
            return {
                "total_cached_items": 0,
                "redis_connected": False,
                "error": str(e)
            }

    async def clear_all(self) -> int:
        """모든 캐시 삭제 (주의!)"""
        if not self.redis:
            return 0

        try:
            pattern = "stock_cache:*"
            keys = await self.redis.keys(pattern)

            if keys:
                deleted = await self.redis.delete(*keys)
                logger.warning(f"[Cache] CLEAR_ALL: {deleted} keys deleted")
                return deleted
            else:
                logger.info(f"[Cache] CLEAR_ALL: No keys to delete")
                return 0
        except Exception as e:
            logger.error(f"[Cache] Clear all error: {e}")
            return 0


# ==========================================
# Singleton instance
# ==========================================
_cache_manager_instance = None


def get_cache_manager(redis_client=None) -> CacheManager:
    """캐시 매니저 싱글톤 인스턴스"""
    global _cache_manager_instance

    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(redis_client)
        logger.info("[Cache] CacheManager initialized")

    return _cache_manager_instance
