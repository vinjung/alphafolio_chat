# services/chat/alpha_ai_model/external_apis/search_strategy.py
"""
Cross-Market Search Strategy

Determines optimal search sources based on market and query context.
Supports parallel search across multiple APIs and result merging.
"""
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from config import logger

from .base import APIResponse, APIErrorCode
from .naver_api import NaverAPI
from .serper_api import SerperAPI
from .dart_api import DartAPI


class SearchScope(str, Enum):
    """Search scope types"""
    LOCAL_ONLY = "local_only"        # Korean sources only
    GLOBAL_ONLY = "global_only"      # Global sources only
    CROSS_MARKET = "cross_market"    # Both Korean and Global


class Market(str, Enum):
    """Market types"""
    KR = "KR"
    US = "US"


@dataclass
class SearchPlan:
    """
    Search execution plan

    Attributes:
        scope: Search scope
        primary_sources: Primary APIs to search
        secondary_sources: Secondary APIs for additional context
        queries: Dict of API -> query mappings
    """
    scope: SearchScope
    primary_sources: List[str] = field(default_factory=list)
    secondary_sources: List[str] = field(default_factory=list)
    queries: Dict[str, str] = field(default_factory=dict)


class SearchStrategy:
    """
    Cross-market search strategy planner

    Determines which APIs to use based on:
    - Market (KR/US)
    - Stock type (global exposure, local only)
    - Query intent (news, analysis, disclosure)

    Supports:
    - Korean stocks with global perspective
    - US stocks with Korean perspective
    - Parallel search execution
    - Result merging and deduplication
    """

    # Korean stocks with high global exposure (automatically search global sources)
    GLOBAL_EXPOSURE_KR = {
        "005930": "Samsung Electronics",
        "000660": "SK Hynix",
        "005380": "Hyundai Motor",
        "000270": "Kia",
        "373220": "LG Energy Solution",
        "035420": "Naver",
        "035720": "Kakao",
        "207940": "Samsung Biologics",
        "068270": "Celltrion",
        "005490": "POSCO Holdings",
        "006400": "Samsung SDI",
        "051910": "LG Chem",
        "003670": "POSCO Future M",
        "012330": "Hyundai Mobis",
        "028260": "Samsung C&T"
    }

    # US stocks popular among Korean investors (automatically add Korean perspective)
    POPULAR_US_IN_KR = {
        "TSLA": "Tesla",
        "AAPL": "Apple",
        "NVDA": "NVIDIA",
        "MSFT": "Microsoft",
        "AMZN": "Amazon",
        "GOOGL": "Alphabet",
        "META": "Meta",
        "AMD": "AMD",
        "NFLX": "Netflix",
        "COIN": "Coinbase",
        "PLTR": "Palantir",
        "SOXL": "SOXL",
        "TQQQ": "TQQQ",
        "SPY": "SPY",
        "QQQ": "QQQ"
    }

    # Korean to English stock name mapping for global search
    KR_TO_EN_NAMES = {
        "삼성전자": "Samsung Electronics",
        "SK하이닉스": "SK Hynix",
        "현대차": "Hyundai Motor",
        "기아": "Kia",
        "LG에너지솔루션": "LG Energy Solution",
        "네이버": "Naver",
        "카카오": "Kakao",
        "삼성바이오로직스": "Samsung Biologics",
        "셀트리온": "Celltrion",
        "포스코홀딩스": "POSCO Holdings",
        "삼성SDI": "Samsung SDI",
        "LG화학": "LG Chem",
        "현대모비스": "Hyundai Mobis"
    }

    def __init__(self):
        """Initialize search strategy with API clients"""
        self.naver = NaverAPI()
        self.serper = SerperAPI()
        self.dart = DartAPI()
        logger.info("[SearchStrategy] Initialized")

    async def close(self):
        """Close all API clients"""
        await asyncio.gather(
            self.naver.close(),
            self.serper.close(),
            self.dart.close()
        )

    def plan_search(
        self,
        query: str,
        market: Market,
        stock_code: str = None,
        stock_name: str = None,
        include_disclosure: bool = False,
        force_cross_market: bool = False
    ) -> SearchPlan:
        """
        Create a search plan based on context

        Args:
            query: Search query
            market: Market type (KR/US)
            stock_code: Stock code (optional)
            stock_name: Stock name (optional)
            include_disclosure: Include DART disclosures
            force_cross_market: Force cross-market search

        Returns:
            SearchPlan with sources and queries
        """
        plan = SearchPlan(scope=SearchScope.LOCAL_ONLY)

        if market == Market.KR:
            # Korean stock
            plan.primary_sources = ["naver"]
            plan.queries["naver"] = query

            # Check if global exposure stock or forced cross-market
            is_global_exposure = (
                stock_code in self.GLOBAL_EXPOSURE_KR or
                stock_name in self.KR_TO_EN_NAMES or
                force_cross_market
            )

            if is_global_exposure:
                plan.scope = SearchScope.CROSS_MARKET
                plan.secondary_sources = ["serper"]

                # Get English name for global search
                en_name = None
                if stock_code and stock_code in self.GLOBAL_EXPOSURE_KR:
                    en_name = self.GLOBAL_EXPOSURE_KR[stock_code]
                elif stock_name and stock_name in self.KR_TO_EN_NAMES:
                    en_name = self.KR_TO_EN_NAMES[stock_name]

                if en_name:
                    plan.queries["serper"] = f"{en_name} stock news"
                else:
                    plan.queries["serper"] = query

            # Add DART if requested
            if include_disclosure:
                if "dart" not in plan.primary_sources:
                    plan.primary_sources.append("dart")
                plan.queries["dart"] = stock_name or query

        else:
            # US stock
            plan.primary_sources = ["serper"]
            plan.queries["serper"] = query

            # Check if popular in Korea
            is_popular_in_kr = (
                stock_code in self.POPULAR_US_IN_KR or
                force_cross_market
            )

            if is_popular_in_kr:
                plan.scope = SearchScope.CROSS_MARKET
                plan.secondary_sources = ["naver"]

                # Convert to Korean search query
                kr_query = self._convert_to_korean_query(query, stock_code, stock_name)
                plan.queries["naver"] = kr_query

        logger.info(f"[SearchStrategy] Plan created: {plan.scope.value}, "
                   f"primary={plan.primary_sources}, secondary={plan.secondary_sources}")

        return plan

    def _convert_to_korean_query(
        self,
        query: str,
        stock_code: str = None,
        stock_name: str = None
    ) -> str:
        """
        Convert English query to Korean for Naver search

        Args:
            query: Original query
            stock_code: Stock code
            stock_name: Stock name

        Returns:
            Korean search query
        """
        # Get Korean representation
        kr_name = None
        if stock_code and stock_code in self.POPULAR_US_IN_KR:
            en_name = self.POPULAR_US_IN_KR[stock_code]
            kr_name = stock_code  # Use symbol for Korean search
        elif stock_name:
            kr_name = stock_name

        if kr_name:
            return f"{kr_name} 주가 전망"
        else:
            return f"{query} 주식"

    async def execute_search(
        self,
        plan: SearchPlan,
        num_results: int = 10
    ) -> Dict[str, APIResponse]:
        """
        Execute search plan

        Args:
            plan: SearchPlan to execute
            num_results: Number of results per source

        Returns:
            Dict of source -> APIResponse
        """
        results = {}
        tasks = []

        # Create tasks for all sources
        all_sources = plan.primary_sources + plan.secondary_sources

        for source in all_sources:
            query = plan.queries.get(source, "")
            if not query:
                continue

            if source == "naver":
                tasks.append(("naver", self.naver.search_news(query, display=num_results)))
            elif source == "serper":
                tasks.append(("serper", self.serper.search_news(query, num=num_results)))
            elif source == "dart":
                tasks.append(("dart", self.dart.search_disclosures(corp_name=query, page_count=num_results)))

        # Execute in parallel
        if tasks:
            logger.info(f"[SearchStrategy] Executing {len(tasks)} searches in parallel")

            responses = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )

            for (source, _), response in zip(tasks, responses):
                if isinstance(response, Exception):
                    logger.error(f"[SearchStrategy] {source} failed: {response}")
                    results[source] = APIResponse.error_response(
                        source,
                        str(response),
                        APIErrorCode.UNKNOWN_ERROR,
                        plan.queries.get(source, "")
                    )
                else:
                    results[source] = response

        return results

    async def search(
        self,
        query: str,
        market: Market = Market.KR,
        stock_code: str = None,
        stock_name: str = None,
        include_disclosure: bool = False,
        num_results: int = 10
    ) -> Dict[str, APIResponse]:
        """
        Convenience method: plan and execute search in one call

        Args:
            query: Search query
            market: Market type
            stock_code: Stock code (optional)
            stock_name: Stock name (optional)
            include_disclosure: Include DART disclosures
            num_results: Number of results per source

        Returns:
            Dict of source -> APIResponse
        """
        plan = self.plan_search(
            query=query,
            market=market,
            stock_code=stock_code,
            stock_name=stock_name,
            include_disclosure=include_disclosure
        )

        return await self.execute_search(plan, num_results)

    def merge_results(
        self,
        results: Dict[str, APIResponse],
        primary_weight: float = 0.7,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Merge results from multiple sources

        Args:
            results: Dict of source -> APIResponse
            primary_weight: Weight for primary sources (higher = prioritize primary)
            max_results: Maximum merged results

        Returns:
            Merged and deduplicated results list
        """
        merged = []
        seen_titles = set()

        # Separate primary and secondary results
        for source, response in results.items():
            if not response.success:
                continue

            for item in response.data:
                title = item.get("title", "").lower()

                # Simple deduplication by title
                if title and title in seen_titles:
                    continue
                seen_titles.add(title)

                # Add source info
                item["_source"] = source
                item["_is_primary"] = source in ["naver", "serper"]  # First API is primary

                merged.append(item)

        # Sort: primary first, then by date if available
        merged.sort(
            key=lambda x: (
                0 if x.get("_is_primary") else 1,
                x.get("pub_date", x.get("date", ""))
            ),
            reverse=True
        )

        return merged[:max_results]

    def get_available_sources(self) -> Dict[str, bool]:
        """
        Get availability status of all API sources

        Returns:
            Dict of source -> is_available
        """
        return {
            "naver": self.naver.is_available,
            "serper": self.serper.is_available,
            "dart": self.dart.is_available
        }

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
