# services/chat/alpha_ai_model/stock_resolver/types.py
"""
Stock Resolver Type Definitions

Defines data types for stock resolution:
- StockInfo: Stock information container
- MatchResult: Matching result with confidence
- Market: Market enumeration (KR, US)
"""
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class Market(Enum):
    """Stock market enumeration"""
    KR = "KR"
    US = "US"


@dataclass
class StockInfo:
    """
    Stock information container

    Attributes:
        symbol: Stock code (e.g., "005930", "AAPL")
        stock_name: Primary name (Korean for KR, English for US)
        stock_name_kr: Korean name (for US stocks)
        stock_name_eng: English name (for KR stocks)
        market: Market type (KR or US)
        aliases: List of alternative names
    """
    symbol: str
    stock_name: str
    stock_name_kr: Optional[str] = None
    stock_name_eng: Optional[str] = None
    market: Market = Market.KR
    aliases: List[str] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []

    def get_all_searchable_names(self) -> List[str]:
        """
        Get all searchable names for this stock

        Returns:
            List of all names including stock_name, stock_name_kr, stock_name_eng, and aliases
        """
        names = [self.stock_name]

        if self.stock_name_kr:
            names.append(self.stock_name_kr)

        if self.stock_name_eng:
            names.append(self.stock_name_eng)

        names.extend(self.aliases)

        return names


@dataclass
class MatchResult:
    """
    Stock matching result

    Attributes:
        stock: Matched stock information
        method: Matching method used ("exact", "alias", "partial", "fuzzy", "llm")
        confidence: Confidence score (0.0 ~ 1.0)
        matched_term: The term that was matched
    """
    stock: StockInfo
    method: str
    confidence: float
    matched_term: str

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "symbol": self.stock.symbol,
            "stock_name": self.stock.stock_name,
            "stock_name_kr": self.stock.stock_name_kr,
            "stock_name_eng": self.stock.stock_name_eng,
            "market": self.stock.market.value,
            "method": self.method,
            "confidence": self.confidence,
            "matched_term": self.matched_term
        }
