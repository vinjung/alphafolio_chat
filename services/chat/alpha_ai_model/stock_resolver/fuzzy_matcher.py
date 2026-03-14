# services/chat/alpha_ai_model/stock_resolver/fuzzy_matcher.py
"""
Fuzzy Matching for Stock Names using rapidfuzz

Provides fuzzy string matching capabilities:
- find_best_match: Find the best matching stock
- select_best: Select best from candidates
- Korean jamo-based matching for better Korean text handling
"""
from typing import Optional, List, Tuple
from config import logger

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("[FuzzyMatcher] rapidfuzz not installed. Fuzzy matching disabled.")

from .types import StockInfo, MatchResult, Market
from .korean_utils import decompose_korean, is_korean


class FuzzyMatcher:
    """
    Fuzzy string matching using rapidfuzz

    Matching algorithms:
    1. WRatio: Weighted ratio (best general purpose)
    2. partial_ratio: Partial string matching
    3. token_sort_ratio: Token-based matching
    4. Korean jamo decomposition matching
    """

    def __init__(self):
        self.kr_choices: List[Tuple[str, StockInfo]] = []
        self.us_choices: List[Tuple[str, StockInfo]] = []
        self._initialized = False

    def build_index(
        self,
        kr_stocks: List[StockInfo],
        us_stocks: List[StockInfo]
    ) -> None:
        """
        Build fuzzy search index

        Args:
            kr_stocks: List of Korean stocks
            us_stocks: List of US stocks
        """
        self.kr_choices = self._build_choices(kr_stocks)
        self.us_choices = self._build_choices(us_stocks)
        self._initialized = True

        logger.info(f"[FuzzyMatcher] Index built: KR={len(self.kr_choices)}, US={len(self.us_choices)}")

    def _build_choices(self, stocks: List[StockInfo]) -> List[Tuple[str, StockInfo]]:
        """
        Build choice list for fuzzy matching

        Each stock generates multiple searchable strings.
        """
        choices = []

        for stock in stocks:
            # Primary name
            choices.append((stock.stock_name, stock))

            # Korean name (for US stocks)
            if stock.stock_name_kr:
                choices.append((stock.stock_name_kr, stock))

            # English name (for KR stocks)
            if stock.stock_name_eng:
                choices.append((stock.stock_name_eng, stock))

            # Aliases
            for alias in stock.aliases:
                choices.append((alias, stock))

        return choices

    def find_best_match(
        self,
        query: str,
        market: Optional[Market] = None,
        threshold: float = 0.80
    ) -> Optional[MatchResult]:
        """
        Find the best fuzzy match for a query

        Args:
            query: Search query
            market: Optional market filter
            threshold: Minimum similarity score (0.0 ~ 1.0)

        Returns:
            MatchResult if match found above threshold, None otherwise
        """
        if not RAPIDFUZZ_AVAILABLE:
            logger.warning("[FuzzyMatcher] rapidfuzz not available")
            return None

        if not self._initialized:
            logger.warning("[FuzzyMatcher] Not initialized")
            return None

        choices = self._get_choices_by_market(market)

        if not choices:
            return None

        # Extract just the strings for rapidfuzz
        choice_strings = [c[0] for c in choices]

        # Use WRatio for best general purpose matching
        # rapidfuzz uses 0-100 scale
        result = process.extractOne(
            query,
            choice_strings,
            scorer=fuzz.WRatio,
            score_cutoff=threshold * 100
        )

        # If no match found, try Korean jamo matching for Korean queries
        if result is None and is_korean(query):
            result = self._korean_fuzzy_match(query, choices, threshold)

        if result:
            matched_string, score, index = result
            stock = choices[index][1]

            return MatchResult(
                stock=stock,
                method="fuzzy",
                confidence=score / 100.0,
                matched_term=matched_string
            )

        return None

    def _korean_fuzzy_match(
        self,
        query: str,
        choices: List[Tuple[str, StockInfo]],
        threshold: float
    ) -> Optional[Tuple[str, float, int]]:
        """
        Korean-specific fuzzy matching using jamo decomposition

        Decomposes Hangul into jamo for better partial matching.
        Example: "삼전" -> "ㅅㅏㅁㅈㅓㄴ" matches "삼성전자" -> "ㅅㅏㅁㅅㅓㅇㅈㅓㄴㅈㅏ"
        """
        if not RAPIDFUZZ_AVAILABLE:
            return None

        query_decomposed = decompose_korean(query)

        best_score = 0
        best_result = None

        for idx, (choice_str, stock) in enumerate(choices):
            if not is_korean(choice_str):
                continue

            choice_decomposed = decompose_korean(choice_str)

            # Use partial_ratio for substring matching
            score = fuzz.partial_ratio(query_decomposed, choice_decomposed)

            if score > best_score and score >= threshold * 100:
                best_score = score
                best_result = (choice_str, score, idx)

        return best_result

    def select_best(
        self,
        query: str,
        candidates: List[MatchResult]
    ) -> Optional[MatchResult]:
        """
        Select the best match from a list of candidates

        Args:
            query: Original search query
            candidates: List of candidate matches

        Returns:
            Best matching MatchResult
        """
        if not candidates:
            return None

        if not RAPIDFUZZ_AVAILABLE:
            # Fall back to first candidate
            return candidates[0]

        best_score = 0
        best_result = None

        for candidate in candidates:
            score = fuzz.WRatio(query, candidate.matched_term)

            if score > best_score:
                best_score = score
                best_result = candidate

        if best_result:
            # Update confidence with fuzzy score
            best_result.confidence = best_score / 100.0
            best_result.method = "fuzzy"

        return best_result

    def find_similar(
        self,
        query: str,
        market: Optional[Market] = None,
        limit: int = 5,
        threshold: float = 0.60
    ) -> List[MatchResult]:
        """
        Find multiple similar matches

        Args:
            query: Search query
            market: Optional market filter
            limit: Maximum number of results
            threshold: Minimum similarity score

        Returns:
            List of MatchResults sorted by confidence
        """
        if not RAPIDFUZZ_AVAILABLE:
            return []

        if not self._initialized:
            return []

        choices = self._get_choices_by_market(market)

        if not choices:
            return []

        choice_strings = [c[0] for c in choices]

        # Get top matches
        results = process.extract(
            query,
            choice_strings,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=threshold * 100
        )

        match_results = []
        for matched_string, score, index in results:
            stock = choices[index][1]
            match_results.append(MatchResult(
                stock=stock,
                method="fuzzy",
                confidence=score / 100.0,
                matched_term=matched_string
            ))

        return match_results

    def _get_choices_by_market(self, market: Optional[Market]) -> List[Tuple[str, StockInfo]]:
        """Get choices filtered by market"""
        if market == Market.KR:
            return self.kr_choices
        elif market == Market.US:
            return self.us_choices
        else:
            return self.kr_choices + self.us_choices

    def get_stats(self) -> dict:
        """Get matcher statistics"""
        return {
            "kr_choices": len(self.kr_choices),
            "us_choices": len(self.us_choices),
            "initialized": self._initialized,
            "rapidfuzz_available": RAPIDFUZZ_AVAILABLE
        }
