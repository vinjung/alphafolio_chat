# services/chat/alpha_ai_model/stock_resolver/resolver.py
"""
Stock Resolver - Main class for resolving stock names to symbols

Hybrid matching strategy:
1. Exact match (O(1)) - stock_name, stock_name_kr, stock_name_eng
2. Alias match (O(1)) - aliases array
3. Partial match (O(n)) - substring search
4. Fuzzy match (O(n)) - rapidfuzz similarity
5. LLM inference (optional) - last resort
"""
from typing import Optional, List, Dict, Any
from config import logger

from .types import StockInfo, MatchResult, Market
from .cache import StockCache
from .fuzzy_matcher import FuzzyMatcher


class StockResolver:
    """
    Stock name to symbol resolver

    Singleton pattern for efficient caching.
    Initialize once at server startup, then use throughout the application.
    """

    _instance: Optional['StockResolver'] = None

    def __init__(self):
        self.cache = StockCache()
        self.fuzzy_matcher = FuzzyMatcher()
        self._initialized = False
        self._kr_stock_count = 0
        self._us_stock_count = 0

    @classmethod
    def get_instance(cls) -> 'StockResolver':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)"""
        cls._instance = None

    async def initialize(self, force: bool = False) -> None:
        """
        Initialize resolver by loading stock data from database

        Args:
            force: Force re-initialization even if already initialized
        """
        if self._initialized and not force:
            logger.debug("[StockResolver] Already initialized, skipping")
            return

        logger.info("[StockResolver] Initializing...")

        try:
            # Load stocks from database
            kr_stocks = await self._load_kr_stocks()
            us_stocks = await self._load_us_stocks()

            # Build indexes
            self.cache.build_index(kr_stocks, us_stocks)
            self.fuzzy_matcher.build_index(kr_stocks, us_stocks)

            self._kr_stock_count = len(kr_stocks)
            self._us_stock_count = len(us_stocks)
            self._initialized = True

            logger.info(f"[StockResolver] Initialized: KR={self._kr_stock_count}, US={self._us_stock_count}")

        except Exception as e:
            logger.error(f"[StockResolver] Initialization failed: {e}")
            raise

    async def resolve(
        self,
        query: str,
        market: Optional[Market] = None
    ) -> Optional[MatchResult]:
        """
        Resolve stock name to symbol

        Args:
            query: User input (e.g., "삼성전자", "Apple", "삼전", "AAPL")
            market: Optional market filter (KR or US)

        Returns:
            MatchResult if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        query = query.strip()
        if not query:
            return None

        # 1. Exact match (O(1))
        result = self.cache.exact_lookup(query, market)
        if result:
            logger.debug(f"[StockResolver] Exact match: '{query}' -> {result.stock.symbol}")
            return result

        # 2. Alias match (O(1))
        result = self.cache.alias_lookup(query, market)
        if result:
            logger.debug(f"[StockResolver] Alias match: '{query}' -> {result.stock.symbol}")
            return result

        # 3. Partial match (O(n))
        candidates = self.cache.partial_lookup(query, market, max_results=5)
        if len(candidates) == 1:
            logger.debug(f"[StockResolver] Partial match: '{query}' -> {candidates[0].stock.symbol}")
            return candidates[0]
        elif len(candidates) > 1:
            # Multiple candidates - use fuzzy to select best
            result = self.fuzzy_matcher.select_best(query, candidates)
            if result:
                logger.debug(f"[StockResolver] Partial+Fuzzy match: '{query}' -> {result.stock.symbol}")
                return result

        # 4. Fuzzy match (O(n))
        result = self.fuzzy_matcher.find_best_match(query, market, threshold=0.80)
        if result:
            logger.debug(f"[StockResolver] Fuzzy match: '{query}' -> {result.stock.symbol} "
                        f"(confidence={result.confidence:.2f})")
            return result

        # 5. LLM inference (optional, not implemented yet)
        # result = await self._llm_inference(query, market)
        # if result:
        #     return result

        logger.debug(f"[StockResolver] No match found: '{query}'")
        return None

    async def resolve_multiple(
        self,
        queries: List[str],
        market: Optional[Market] = None
    ) -> Dict[str, Optional[MatchResult]]:
        """
        Resolve multiple stock names at once

        Args:
            queries: List of stock names to resolve
            market: Optional market filter

        Returns:
            Dictionary mapping query to MatchResult (or None)
        """
        results = {}
        for query in queries:
            results[query] = await self.resolve(query, market)
        return results

    async def find_similar(
        self,
        query: str,
        market: Optional[Market] = None,
        limit: int = 5
    ) -> List[MatchResult]:
        """
        Find similar stock names (for suggestions)

        Args:
            query: Search query
            market: Optional market filter
            limit: Maximum number of results

        Returns:
            List of similar MatchResults
        """
        if not self._initialized:
            await self.initialize()

        return self.fuzzy_matcher.find_similar(query, market, limit=limit, threshold=0.50)

    async def _load_kr_stocks(self) -> List[StockInfo]:
        """Load Korean stocks from database"""
        from database import db

        if db.pool is None:
            logger.warning("[StockResolver] Database not connected, returning empty list")
            return []

        query = """
            SELECT
                symbol,
                stock_name,
                stock_name_eng,
                COALESCE(aliases, ARRAY[]::TEXT[]) as aliases
            FROM kr_stock_basic
            WHERE symbol IS NOT NULL
              AND stock_name IS NOT NULL
        """

        stocks = []
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(query)

                for row in rows:
                    stock = StockInfo(
                        symbol=row['symbol'],
                        stock_name=row['stock_name'],
                        stock_name_eng=row.get('stock_name_eng'),
                        stock_name_kr=None,  # KR stocks don't need Korean name (already Korean)
                        market=Market.KR,
                        aliases=list(row['aliases']) if row['aliases'] else []
                    )
                    stocks.append(stock)

            logger.info(f"[StockResolver] Loaded {len(stocks)} KR stocks from database")

        except Exception as e:
            logger.error(f"[StockResolver] Failed to load KR stocks: {e}")
            # Return fallback data for critical stocks
            stocks = self._get_fallback_kr_stocks()

        return stocks

    async def _load_us_stocks(self) -> List[StockInfo]:
        """Load US stocks from database"""
        from database import db

        if db.pool is None:
            logger.warning("[StockResolver] Database not connected, returning empty list")
            return []

        query = """
            SELECT
                symbol,
                stock_name,
                COALESCE(stock_name_kr, '') as stock_name_kr,
                COALESCE(aliases, ARRAY[]::TEXT[]) as aliases
            FROM us_stock_basic
            WHERE symbol IS NOT NULL
              AND stock_name IS NOT NULL
        """

        stocks = []
        try:
            async with db.pool.acquire() as conn:
                rows = await conn.fetch(query)

                for row in rows:
                    stock = StockInfo(
                        symbol=row['symbol'],
                        stock_name=row['stock_name'],  # English name
                        stock_name_eng=row['stock_name'],  # Same as stock_name for US
                        stock_name_kr=row['stock_name_kr'] if row['stock_name_kr'] else None,
                        market=Market.US,
                        aliases=list(row['aliases']) if row['aliases'] else []
                    )
                    stocks.append(stock)

            logger.info(f"[StockResolver] Loaded {len(stocks)} US stocks from database")

        except Exception as e:
            logger.error(f"[StockResolver] Failed to load US stocks: {e}")
            # Return fallback data for critical stocks
            stocks = self._get_fallback_us_stocks()

        return stocks

    def _get_fallback_kr_stocks(self) -> List[StockInfo]:
        """Fallback KR stocks when database is unavailable"""
        return [
            StockInfo(symbol="005930", stock_name="삼성전자", stock_name_eng="Samsung Electronics",
                     market=Market.KR, aliases=["삼전", "삼성"]),
            StockInfo(symbol="000660", stock_name="SK하이닉스", stock_name_eng="SK Hynix",
                     market=Market.KR, aliases=["하닉", "에스케이하이닉스"]),
            StockInfo(symbol="373220", stock_name="LG에너지솔루션", stock_name_eng="LG Energy Solution",
                     market=Market.KR, aliases=["LG에솔", "엘지에너지솔루션"]),
            StockInfo(symbol="207940", stock_name="삼성바이오로직스", stock_name_eng="Samsung Biologics",
                     market=Market.KR, aliases=["삼바", "삼성바이오"]),
            StockInfo(symbol="005380", stock_name="현대차", stock_name_eng="Hyundai Motor",
                     market=Market.KR, aliases=["현대자동차", "현차"]),
            StockInfo(symbol="000270", stock_name="기아", stock_name_eng="Kia",
                     market=Market.KR, aliases=["기아차", "기아자동차"]),
            StockInfo(symbol="035420", stock_name="NAVER", stock_name_eng="NAVER",
                     market=Market.KR, aliases=["네이버"]),
            StockInfo(symbol="035720", stock_name="카카오", stock_name_eng="Kakao",
                     market=Market.KR, aliases=["카톡"]),
            StockInfo(symbol="006400", stock_name="삼성SDI", stock_name_eng="Samsung SDI",
                     market=Market.KR, aliases=["삼성에스디아이"]),
            StockInfo(symbol="051910", stock_name="LG화학", stock_name_eng="LG Chem",
                     market=Market.KR, aliases=["엘지화학"]),
        ]

    def _get_fallback_us_stocks(self) -> List[StockInfo]:
        """Fallback US stocks when database is unavailable"""
        return [
            StockInfo(symbol="AAPL", stock_name="Apple Inc.", stock_name_kr="애플",
                     market=Market.US, aliases=["Apple", "애플"]),
            StockInfo(symbol="MSFT", stock_name="Microsoft Corporation", stock_name_kr="마이크로소프트",
                     market=Market.US, aliases=["Microsoft", "MS", "마소"]),
            StockInfo(symbol="GOOGL", stock_name="Alphabet Inc.", stock_name_kr="구글",
                     market=Market.US, aliases=["Google", "구글", "알파벳"]),
            StockInfo(symbol="AMZN", stock_name="Amazon.com, Inc.", stock_name_kr="아마존",
                     market=Market.US, aliases=["Amazon", "아마존"]),
            StockInfo(symbol="TSLA", stock_name="Tesla, Inc.", stock_name_kr="테슬라",
                     market=Market.US, aliases=["Tesla", "테슬라"]),
            StockInfo(symbol="NVDA", stock_name="NVIDIA Corporation", stock_name_kr="엔비디아",
                     market=Market.US, aliases=["NVIDIA", "엔비디아", "엔당"]),
            StockInfo(symbol="META", stock_name="Meta Platforms, Inc.", stock_name_kr="메타",
                     market=Market.US, aliases=["Meta", "Facebook", "메타", "페이스북"]),
            StockInfo(symbol="NFLX", stock_name="Netflix, Inc.", stock_name_kr="넷플릭스",
                     market=Market.US, aliases=["Netflix", "넷플릭스"]),
            StockInfo(symbol="AMD", stock_name="Advanced Micro Devices, Inc.", stock_name_kr="AMD",
                     market=Market.US, aliases=["에이엠디"]),
            StockInfo(symbol="INTC", stock_name="Intel Corporation", stock_name_kr="인텔",
                     market=Market.US, aliases=["Intel", "인텔"]),
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get resolver statistics"""
        cache_stats = self.cache.get_stats()
        fuzzy_stats = self.fuzzy_matcher.get_stats()

        return {
            "initialized": self._initialized,
            "kr_stocks": self._kr_stock_count,
            "us_stocks": self._us_stock_count,
            "cache": cache_stats,
            "fuzzy": fuzzy_stats
        }

    def is_initialized(self) -> bool:
        """Check if resolver is initialized"""
        return self._initialized
