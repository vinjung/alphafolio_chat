# services/chat/alpha_ai_model/stock_resolver/__init__.py
"""
Stock Resolver Module

Provides stock name to symbol resolution with hybrid matching:
- Exact match
- Alias match
- Partial match
- Fuzzy match (rapidfuzz)
- Korean jamo-based matching

Usage:
    from services.chat.alpha_ai_model.stock_resolver import StockResolver, Market

    resolver = StockResolver.get_instance()
    await resolver.initialize()

    result = await resolver.resolve("삼성전자")
    if result:
        print(f"Symbol: {result.stock.symbol}")  # "005930"
        print(f"Method: {result.method}")        # "exact"
        print(f"Confidence: {result.confidence}") # 1.0
"""

from .types import StockInfo, MatchResult, Market
from .resolver import StockResolver
from .cache import StockCache
from .fuzzy_matcher import FuzzyMatcher
from .korean_utils import (
    decompose_korean,
    extract_chosung,
    is_korean,
    normalize_korean
)

__all__ = [
    # Main classes
    "StockResolver",
    "StockCache",
    "FuzzyMatcher",

    # Types
    "StockInfo",
    "MatchResult",
    "Market",

    # Korean utilities
    "decompose_korean",
    "extract_chosung",
    "is_korean",
    "normalize_korean",
]
