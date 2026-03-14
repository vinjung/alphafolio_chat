# services/chat/alpha_ai_model/tools/search_tools.py
"""
Search Tools for Alpha AI

Provides search utilities:
- Stock name/code lookup
- Schema search
- Term mapping search
"""
from typing import List, Dict, Any, Optional
from config import logger


class SearchTools:
    """Search utility tools for Alpha AI"""

    # Common Korean stock name mappings
    STOCK_MAPPINGS: Dict[str, Dict[str, str]] = {
        "삼성전자": {"code": "005930", "market": "KR"},
        "sk하이닉스": {"code": "000660", "market": "KR"},
        "네이버": {"code": "035420", "market": "KR"},
        "카카오": {"code": "035720", "market": "KR"},
        "현대차": {"code": "005380", "market": "KR"},
        "기아": {"code": "000270", "market": "KR"},
        "셀트리온": {"code": "068270", "market": "KR"},
        "lg에너지솔루션": {"code": "373220", "market": "KR"},
        "삼성바이오로직스": {"code": "207940", "market": "KR"},
        "포스코홀딩스": {"code": "005490", "market": "KR"},
    }

    # US stock mappings
    US_STOCK_MAPPINGS: Dict[str, Dict[str, str]] = {
        "apple": {"code": "AAPL", "market": "US"},
        "애플": {"code": "AAPL", "market": "US"},
        "microsoft": {"code": "MSFT", "market": "US"},
        "마이크로소프트": {"code": "MSFT", "market": "US"},
        "google": {"code": "GOOGL", "market": "US"},
        "구글": {"code": "GOOGL", "market": "US"},
        "amazon": {"code": "AMZN", "market": "US"},
        "아마존": {"code": "AMZN", "market": "US"},
        "tesla": {"code": "TSLA", "market": "US"},
        "테슬라": {"code": "TSLA", "market": "US"},
        "nvidia": {"code": "NVDA", "market": "US"},
        "엔비디아": {"code": "NVDA", "market": "US"},
        "meta": {"code": "META", "market": "US"},
        "메타": {"code": "META", "market": "US"},
    }

    @staticmethod
    def find_stock(query: str) -> Optional[Dict[str, str]]:
        """
        Find stock by name

        Args:
            query: Stock name to search

        Returns:
            Dict with code and market, or None
        """
        query_lower = query.lower().strip()

        # Check Korean stocks
        for name, info in SearchTools.STOCK_MAPPINGS.items():
            if name in query_lower or query_lower in name:
                return info

        # Check US stocks
        for name, info in SearchTools.US_STOCK_MAPPINGS.items():
            if name in query_lower or query_lower in name:
                return info

        return None

    @staticmethod
    def detect_market(query: str) -> str:
        """
        Detect market from query

        Args:
            query: User query

        Returns:
            'KR' or 'US'
        """
        query_lower = query.lower()

        us_keywords = [
            "미국", "나스닥", "nasdaq", "nyse", "s&p", "다우",
            "애플", "테슬라", "구글", "아마존", "마이크로소프트", "엔비디아"
        ]

        for keyword in us_keywords:
            if keyword in query_lower:
                return "US"

        return "KR"

    @staticmethod
    def extract_indicators(query: str) -> List[str]:
        """
        Extract technical indicators from query

        Args:
            query: User query

        Returns:
            List of indicator names
        """
        query_lower = query.lower()

        indicator_keywords = {
            "rsi": "RSI",
            "macd": "MACD",
            "볼린저": "Bollinger",
            "이평": "MA",
            "이동평균": "MA",
            "골든크로스": "Golden Cross",
            "데드크로스": "Dead Cross",
            "거래량": "volume",
            "거래대금": "trading_value",
            "시총": "market_cap",
            "시가총액": "market_cap",
            "per": "PER",
            "pbr": "PBR",
            "배당": "dividend",
        }

        found = []
        for keyword, indicator in indicator_keywords.items():
            if keyword in query_lower:
                found.append(indicator)

        return found
