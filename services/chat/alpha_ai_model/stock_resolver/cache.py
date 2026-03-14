# services/chat/alpha_ai_model/stock_resolver/cache.py
"""
Stock Cache for Fast Lookup

Provides in-memory caching for stock data:
- exact_index: Hash index for exact name matching (O(1))
- alias_index: Hash index for alias matching (O(1))
- Stock lists for partial and fuzzy matching
"""
from typing import Optional, List, Dict
from .types import StockInfo, MatchResult, Market


class StockCache:
    """
    Stock data in-memory cache

    Index structures:
    - exact_index: {normalized_name: StockInfo}
    - alias_index: {alias: StockInfo}
    - symbol_index: {symbol: StockInfo}
    - kr_stocks: List of all KR stocks
    - us_stocks: List of all US stocks
    """

    def __init__(self):
        # Hash indexes for O(1) lookup
        self.exact_index: Dict[str, StockInfo] = {}
        self.alias_index: Dict[str, StockInfo] = {}
        self.symbol_index: Dict[str, StockInfo] = {}

        # Lists for partial/fuzzy matching
        self.kr_stocks: List[StockInfo] = []
        self.us_stocks: List[StockInfo] = []

        self._initialized = False

    def build_index(
        self,
        kr_stocks: List[StockInfo],
        us_stocks: List[StockInfo]
    ) -> None:
        """
        Build search indexes from stock lists

        Args:
            kr_stocks: List of Korean stocks
            us_stocks: List of US stocks
        """
        # Clear existing indexes
        self.exact_index.clear()
        self.alias_index.clear()
        self.symbol_index.clear()

        # Store stock lists
        self.kr_stocks = kr_stocks
        self.us_stocks = us_stocks

        all_stocks = kr_stocks + us_stocks

        for stock in all_stocks:
            # Symbol index (always exact)
            self._add_to_symbol_index(stock.symbol, stock)

            # Exact name index
            self._add_to_exact_index(stock.stock_name.lower(), stock)

            # Korean name (for US stocks)
            if stock.stock_name_kr:
                self._add_to_exact_index(stock.stock_name_kr.lower(), stock)

            # English name (for KR stocks)
            if stock.stock_name_eng:
                self._add_to_exact_index(stock.stock_name_eng.lower(), stock)

            # Alias index
            for alias in stock.aliases:
                self._add_to_alias_index(alias.lower(), stock)

        self._initialized = True

    def _add_to_symbol_index(self, symbol: str, stock: StockInfo) -> None:
        """Add to symbol index"""
        # Store both original and lowercase
        self.symbol_index[symbol] = stock
        self.symbol_index[symbol.lower()] = stock
        self.symbol_index[symbol.upper()] = stock

    def _add_to_exact_index(self, key: str, stock: StockInfo) -> None:
        """Add to exact match index"""
        key = key.strip()
        if key:
            self.exact_index[key] = stock

    def _add_to_alias_index(self, key: str, stock: StockInfo) -> None:
        """Add to alias index"""
        key = key.strip()
        if key:
            self.alias_index[key] = stock

    def symbol_lookup(self, symbol: str) -> Optional[MatchResult]:
        """
        Lookup by symbol directly

        Args:
            symbol: Stock symbol (e.g., "AAPL", "005930")

        Returns:
            MatchResult if found, None otherwise
        """
        stock = self.symbol_index.get(symbol)

        if stock:
            return MatchResult(
                stock=stock,
                method="symbol",
                confidence=1.0,
                matched_term=symbol
            )
        return None

    def exact_lookup(
        self,
        query: str,
        market: Optional[Market] = None
    ) -> Optional[MatchResult]:
        """
        Exact name matching lookup (O(1))

        Args:
            query: Search query
            market: Optional market filter

        Returns:
            MatchResult if exact match found, None otherwise
        """
        key = query.lower().strip()

        # First check symbol index
        symbol_result = self.symbol_lookup(query)
        if symbol_result:
            if market is None or symbol_result.stock.market == market:
                return symbol_result

        # Then check exact name index
        stock = self.exact_index.get(key)

        if stock and (market is None or stock.market == market):
            return MatchResult(
                stock=stock,
                method="exact",
                confidence=1.0,
                matched_term=query
            )
        return None

    def alias_lookup(
        self,
        query: str,
        market: Optional[Market] = None
    ) -> Optional[MatchResult]:
        """
        Alias matching lookup (O(1))

        Args:
            query: Search query
            market: Optional market filter

        Returns:
            MatchResult if alias match found, None otherwise
        """
        key = query.lower().strip()
        stock = self.alias_index.get(key)

        if stock and (market is None or stock.market == market):
            return MatchResult(
                stock=stock,
                method="alias",
                confidence=1.0,
                matched_term=query
            )
        return None

    def partial_lookup(
        self,
        query: str,
        market: Optional[Market] = None,
        max_results: int = 10
    ) -> List[MatchResult]:
        """
        Partial string matching lookup (O(n))

        Args:
            query: Search query
            market: Optional market filter
            max_results: Maximum number of results to return

        Returns:
            List of MatchResults for partial matches
        """
        query_lower = query.lower().strip()
        results = []

        stocks = self._get_stocks_by_market(market)

        for stock in stocks:
            if len(results) >= max_results:
                break

            matched_term = None

            # Check stock_name
            if query_lower in stock.stock_name.lower():
                matched_term = stock.stock_name

            # Check stock_name_kr
            elif stock.stock_name_kr and query_lower in stock.stock_name_kr.lower():
                matched_term = stock.stock_name_kr

            # Check stock_name_eng
            elif stock.stock_name_eng and query_lower in stock.stock_name_eng.lower():
                matched_term = stock.stock_name_eng

            # Check aliases
            else:
                for alias in stock.aliases:
                    if query_lower in alias.lower():
                        matched_term = alias
                        break

            if matched_term:
                results.append(MatchResult(
                    stock=stock,
                    method="partial",
                    confidence=0.9,
                    matched_term=matched_term
                ))

        return results

    def _get_stocks_by_market(self, market: Optional[Market]) -> List[StockInfo]:
        """Get stock list filtered by market"""
        if market == Market.KR:
            return self.kr_stocks
        elif market == Market.US:
            return self.us_stocks
        else:
            return self.kr_stocks + self.us_stocks

    def get_all_stocks(self, market: Optional[Market] = None) -> List[StockInfo]:
        """Get all stocks, optionally filtered by market"""
        return self._get_stocks_by_market(market)

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "kr_stocks": len(self.kr_stocks),
            "us_stocks": len(self.us_stocks),
            "exact_index_size": len(self.exact_index),
            "alias_index_size": len(self.alias_index),
            "symbol_index_size": len(self.symbol_index),
            "initialized": self._initialized
        }
