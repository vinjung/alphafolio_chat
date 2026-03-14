# services/chat/alpha_ai_model/rag/query_expander.py
"""
Query Expander for Alpha AI

Expands user queries with synonyms, related terms, and query rewriting.
Improves retrieval accuracy by generating multiple query variations.
"""
from typing import List, Dict, Any, Optional
from config import logger

from core.llm.factory import get_llm, LLMProvider


class QueryExpander:
    """
    Query Expansion Service

    Expands queries using:
    1. Synonym expansion (static dictionary)
    2. Related term expansion
    3. LLM-based query rewriting
    """

    # Static synonym mappings
    SYNONYMS: Dict[str, List[str]] = {
        # Price terms
        "현재가": ["종가", "close", "가격", "주가"],
        "종가": ["현재가", "close", "가격"],
        "시가": ["open", "시초가"],
        "고가": ["high", "최고가"],
        "저가": ["low", "최저가"],

        # Volume/Value terms
        "거래량": ["volume", "거래수량", "매매량", "볼륨"],
        "거래대금": ["거래금액", "매매대금", "거래액", "trading_value"],
        "시가총액": ["시총", "market_cap", "마켓캡", "시장가치"],
        "시총": ["시가총액", "market_cap"],

        # Technical indicators
        "rsi": ["알에스아이", "상대강도지수", "RSI"],
        "macd": ["맥디", "MACD", "이동평균수렴확산"],
        "볼린저밴드": ["볼린저", "bollinger", "BB"],
        "이동평균": ["이평선", "이평", "MA", "moving average"],
        "골든크로스": ["golden cross", "황금교차", "정배열 전환"],
        "데드크로스": ["dead cross", "사망교차", "역배열 전환"],

        # Investor types
        "외국인": ["외인", "foreign", "외국인투자자"],
        "기관": ["기관투자자", "institution", "기관투자"],
        "개인": ["개미", "individual", "개인투자자", "리테일"],

        # Market terms
        "코스피": ["KOSPI", "유가증권", "거래소"],
        "코스닥": ["KOSDAQ", "코스닥시장"],
        "나스닥": ["NASDAQ", "나스닥시장"],

        # Condition terms
        "상위": ["top", "랭킹", "순위", "최고"],
        "하위": ["bottom", "최저", "worst"],
        "이상": [">=", "초과", "above", "over"],
        "이하": ["<=", "미만", "below", "under"],

        # Analysis terms
        "과매수": ["overbought", "과열", "RSI 70 이상"],
        "과매도": ["oversold", "침체", "RSI 30 이하"],
        "대형주": ["large cap", "시총 대형", "블루칩"],
        "중형주": ["mid cap", "시총 중형"],
        "소형주": ["small cap", "시총 소형"],
    }

    # Query rewriting prompt
    REWRITE_PROMPT = """Rewrite the following stock market query to be clearer and more specific for SQL generation.

Original Query: {query}

Rules:
1. Keep the core intent
2. Expand abbreviations (e.g., "시총" -> "시가총액")
3. Add implicit conditions if clear from context
4. Use standard financial terminology
5. Output only the rewritten query, no explanation

Rewritten Query:"""

    def __init__(self, use_llm: bool = True):
        """
        Initialize QueryExpander

        Args:
            use_llm: Whether to use LLM for query rewriting
        """
        self.use_llm = use_llm
        self.synonyms = self.SYNONYMS
        self._build_reverse_index()
        logger.info("[QueryExpander] Initialized")

    def _build_reverse_index(self) -> None:
        """Build reverse index for synonym lookup"""
        self.reverse_index = {}
        for canonical, synonyms in self.synonyms.items():
            self.reverse_index[canonical.lower()] = canonical
            for syn in synonyms:
                self.reverse_index[syn.lower()] = canonical

    def get_canonical_term(self, term: str) -> str:
        """
        Get canonical form of a term

        Args:
            term: Input term

        Returns:
            Canonical term
        """
        return self.reverse_index.get(term.lower(), term)

    def expand_with_synonyms(self, query: str) -> List[str]:
        """
        Expand query with synonyms

        Args:
            query: Original query

        Returns:
            List of expanded queries
        """
        expanded = [query]
        query_lower = query.lower()

        for term, synonyms in self.synonyms.items():
            if term.lower() in query_lower:
                for syn in synonyms[:2]:  # Limit to top 2 synonyms
                    expanded_query = query_lower.replace(term.lower(), syn.lower())
                    if expanded_query not in expanded:
                        expanded.append(expanded_query)

        return expanded[:5]  # Limit total expansions

    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query

        Args:
            query: User query

        Returns:
            List of keywords
        """
        keywords = []
        query_lower = query.lower()

        # Check all known terms
        for term in self.synonyms.keys():
            if term.lower() in query_lower:
                keywords.append(term)

        # Extract numbers (potential limits, thresholds)
        import re
        numbers = re.findall(r'\d+', query)
        keywords.extend(numbers)

        return keywords

    async def rewrite_with_llm(
        self,
        query: str,
        provider: str = None,
        model: str = None
    ) -> str:
        """
        Rewrite query using LLM for clarity

        Args:
            query: Original query
            provider: LLM provider
            model: Model name

        Returns:
            Rewritten query
        """
        if not self.use_llm:
            return query

        try:
            llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
            llm = get_llm(llm_provider, model_name=model)

            prompt = self.REWRITE_PROMPT.format(query=query)
            response = await llm.ainvoke(prompt)
            rewritten = response.content if hasattr(response, 'content') else str(response)

            # Clean up response
            rewritten = rewritten.strip()
            if rewritten and len(rewritten) > 5:
                logger.info(f"[QueryExpander] Rewritten: {query} -> {rewritten}")
                return rewritten

            return query

        except Exception as e:
            logger.warning(f"[QueryExpander] LLM rewrite failed: {e}")
            return query

    async def expand(
        self,
        query: str,
        use_synonyms: bool = True,
        use_rewrite: bool = False,
        provider: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Full query expansion

        Args:
            query: Original query
            use_synonyms: Whether to use synonym expansion
            use_rewrite: Whether to use LLM rewriting
            provider: LLM provider
            model: Model name

        Returns:
            Expansion result dictionary
        """
        result = {
            "original": query,
            "rewritten": query,
            "expanded": [query],
            "keywords": []
        }

        # Extract keywords
        result["keywords"] = self.extract_keywords(query)

        # LLM rewriting (if enabled)
        if use_rewrite and self.use_llm:
            result["rewritten"] = await self.rewrite_with_llm(query, provider, model)

        # Synonym expansion
        if use_synonyms:
            base_query = result["rewritten"]
            result["expanded"] = self.expand_with_synonyms(base_query)

        logger.info(f"[QueryExpander] Expanded '{query}' to {len(result['expanded'])} variations")
        return result

    def normalize_query(self, query: str) -> str:
        """
        Normalize query by replacing synonyms with canonical terms

        Args:
            query: Original query

        Returns:
            Normalized query
        """
        normalized = query.lower()

        # Sort by length descending to replace longer terms first
        sorted_terms = sorted(self.reverse_index.keys(), key=len, reverse=True)

        for term in sorted_terms:
            if term in normalized:
                canonical = self.reverse_index[term]
                # Only replace if different
                if term != canonical.lower():
                    normalized = normalized.replace(term, canonical.lower())

        return normalized

    def get_related_tables(self, query: str) -> List[str]:
        """
        Get related tables based on query keywords

        Args:
            query: User query

        Returns:
            List of potentially related table names
        """
        tables = set()
        query_lower = query.lower()

        # Keyword to table mapping
        table_keywords = {
            "kr_intraday": ["가격", "종가", "시가", "거래량", "거래대금", "시총"],
            "kr_indicators": ["rsi", "macd", "볼린저", "이평", "기술적", "지표"],
            "kr_individual_investor_daily_trading": ["외국인", "외인", "기관", "개인", "순매수"],
            "kr_stock_grade": ["등급", "점수", "퀀트", "가치", "모멘텀"],
            "us_daily": ["미국", "나스닥", "apple", "tesla", "nvidia"],
            "us_indicators": ["us rsi", "us macd", "미국 지표"],
            "market_index": ["코스피", "코스닥", "나스닥", "지수"],
        }

        for table, keywords in table_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    tables.add(table)
                    break

        return list(tables)
