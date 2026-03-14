# services/chat/alpha_ai_model/rag/self_query.py
"""
Self-Query Retriever for Alpha AI

Extracts structured filter conditions from natural language queries.
Converts user intent into SQL-compatible filter expressions.
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from config import logger

from core.llm.factory import get_llm, LLMProvider


class FilterOperator(Enum):
    """SQL filter operators"""
    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    BETWEEN = "BETWEEN"


@dataclass
class FilterCondition:
    """Represents a single filter condition"""
    column: str
    operator: FilterOperator
    value: Any
    table: Optional[str] = None

    def to_sql(self) -> str:
        """Convert to SQL WHERE clause fragment"""
        col = f"{self.table}.{self.column}" if self.table else self.column

        if self.operator == FilterOperator.IN:
            values = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in self.value)
            return f"{col} IN ({values})"
        elif self.operator == FilterOperator.NOT_IN:
            values = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in self.value)
            return f"{col} NOT IN ({values})"
        elif self.operator == FilterOperator.LIKE:
            return f"{col} LIKE '%{self.value}%'"
        elif self.operator == FilterOperator.BETWEEN:
            return f"{col} BETWEEN {self.value[0]} AND {self.value[1]}"
        else:
            if isinstance(self.value, str):
                return f"{col} {self.operator.value} '{self.value}'"
            return f"{col} {self.operator.value} {self.value}"


@dataclass
class SortCondition:
    """Represents a sort condition"""
    column: str
    direction: str = "DESC"
    table: Optional[str] = None

    def to_sql(self) -> str:
        """Convert to SQL ORDER BY fragment"""
        col = f"{self.table}.{self.column}" if self.table else self.column
        return f"{col} {self.direction}"


@dataclass
class QueryStructure:
    """Structured query representation"""
    filters: List[FilterCondition]
    sorts: List[SortCondition]
    limit: Optional[int]
    tables: List[str]
    columns: List[str]


class SelfQueryRetriever:
    """
    Self-Query Retriever

    Extracts structured query components from natural language:
    - Filter conditions (WHERE)
    - Sort conditions (ORDER BY)
    - Limit (LIMIT)
    - Required tables and columns
    """

    # Pattern-based extraction rules
    FILTER_PATTERNS = [
        # Number comparisons
        (r'(\w+)\s*(이상|>=|초과)', lambda m: (m.group(1), FilterOperator.GTE)),
        (r'(\w+)\s*(이하|<=|미만)', lambda m: (m.group(1), FilterOperator.LTE)),
        (r'(\w+)\s*(보다\s*크|>)', lambda m: (m.group(1), FilterOperator.GT)),
        (r'(\w+)\s*(보다\s*작|<)', lambda m: (m.group(1), FilterOperator.LT)),

        # RSI conditions
        (r'rsi\s*(\d+)\s*이상', lambda m: ("rsi", FilterOperator.GTE, int(m.group(1)))),
        (r'rsi\s*(\d+)\s*이하', lambda m: ("rsi", FilterOperator.LTE, int(m.group(1)))),
        (r'과매수', lambda m: ("rsi", FilterOperator.GT, 70)),
        (r'과매도', lambda m: ("rsi", FilterOperator.LT, 30)),

        # Market cap
        (r'시총?\s*(\d+)\s*(조|억)\s*이상', None),  # Custom handler
        (r'대형주', lambda m: ("market_cap", FilterOperator.GTE, 10000000000000)),
        (r'중형주', None),  # Custom handler
        (r'소형주', lambda m: ("market_cap", FilterOperator.LT, 1000000000000)),
    ]

    SORT_PATTERNS = [
        (r'(거래대금|거래량|시총|시가총액|등락률)\s*상위', lambda m: (m.group(1), "DESC")),
        (r'(거래대금|거래량|시총|시가총액|등락률)\s*하위', lambda m: (m.group(1), "ASC")),
        (r'상위\s*\d+', lambda m: (None, "DESC")),  # Generic top N
        (r'하위\s*\d+', lambda m: (None, "ASC")),   # Generic bottom N
    ]

    LIMIT_PATTERNS = [
        (r'상위\s*(\d+)', lambda m: int(m.group(1))),
        (r'하위\s*(\d+)', lambda m: int(m.group(1))),
        (r'top\s*(\d+)', lambda m: int(m.group(1))),
        (r'(\d+)\s*개', lambda m: int(m.group(1))),
        (r'(\d+)\s*종목', lambda m: int(m.group(1))),
    ]

    # Column name mappings
    COLUMN_MAP = {
        "거래대금": "trading_value",
        "거래량": "volume",
        "시총": "market_cap",
        "시가총액": "market_cap",
        "등락률": "change_rate",
        "변동률": "change_rate",
        "종가": "close",
        "현재가": "close",
        "rsi": "rsi",
        "macd": "macd",
    }

    # LLM extraction prompt
    EXTRACTION_PROMPT = """Extract structured query conditions from the following stock market query.

Query: {query}

Extract the following in JSON format:
{{
    "filters": [
        {{"column": "column_name", "operator": ">=|<=|>|<|=|IN", "value": value}}
    ],
    "sort_by": {{"column": "column_name", "direction": "DESC|ASC"}},
    "limit": number or null,
    "market": "KR|US"
}}

Available columns:
- Price: close, open, high, low, volume, trading_value, market_cap, change_rate
- Technical: rsi, macd, macd_signal, bb_upper, bb_lower, ma5, ma20, ma60
- Investor: foreign_net_volume, institution_net_volume
- Quant: total_grade, total_score, value_score

Common patterns:
- "시총 1조 이상" -> {{"column": "market_cap", "operator": ">=", "value": 1000000000000}}
- "RSI 30 이하" -> {{"column": "rsi", "operator": "<=", "value": 30}}
- "거래대금 상위 10" -> sort by trading_value DESC, limit 10

Output only valid JSON:"""

    def __init__(self, use_llm: bool = True):
        """
        Initialize SelfQueryRetriever

        Args:
            use_llm: Whether to use LLM for extraction
        """
        self.use_llm = use_llm
        self.column_map = self.COLUMN_MAP
        logger.info("[SelfQueryRetriever] Initialized")

    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract LIMIT from query"""
        query_lower = query.lower()

        for pattern, extractor in self.LIMIT_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                return extractor(match)

        return None

    def _extract_sort(self, query: str) -> Optional[SortCondition]:
        """Extract ORDER BY from query"""
        query_lower = query.lower()

        for pattern, extractor in self.SORT_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                result = extractor(match)
                if result[0]:
                    column = self.column_map.get(result[0], result[0])
                    return SortCondition(column=column, direction=result[1])

        # Default sort by trading_value if "상위" is mentioned
        if "상위" in query_lower:
            return SortCondition(column="trading_value", direction="DESC")

        return None

    def _extract_filters_rule_based(self, query: str) -> List[FilterCondition]:
        """Extract filters using rule-based patterns"""
        filters = []
        query_lower = query.lower()

        # RSI conditions
        if "과매수" in query_lower:
            filters.append(FilterCondition("rsi", FilterOperator.GT, 70))
        if "과매도" in query_lower:
            filters.append(FilterCondition("rsi", FilterOperator.LT, 30))

        # RSI with specific value
        rsi_match = re.search(r'rsi\s*(\d+)\s*(이상|이하)', query_lower)
        if rsi_match:
            value = int(rsi_match.group(1))
            op = FilterOperator.GTE if "이상" in rsi_match.group(2) else FilterOperator.LTE
            filters.append(FilterCondition("rsi", op, value))

        # Market cap conditions
        cap_match = re.search(r'시총?\s*(\d+)\s*(조|억)\s*(이상|이하)?', query_lower)
        if cap_match:
            value = int(cap_match.group(1))
            unit = cap_match.group(2)
            condition = cap_match.group(3) if cap_match.group(3) else "이상"

            # Convert to KRW
            if unit == "조":
                value = value * 1000000000000
            elif unit == "억":
                value = value * 100000000

            op = FilterOperator.GTE if "이상" in condition else FilterOperator.LTE
            filters.append(FilterCondition("market_cap", op, value))

        # Market cap classifications
        if "대형주" in query_lower:
            filters.append(FilterCondition("market_cap", FilterOperator.GTE, 10000000000000))
        if "소형주" in query_lower:
            filters.append(FilterCondition("market_cap", FilterOperator.LT, 1000000000000))

        # Volume conditions
        vol_match = re.search(r'거래량\s*(\d+)\s*(만|억)?\s*(이상|이하)', query_lower)
        if vol_match:
            value = int(vol_match.group(1))
            unit = vol_match.group(2)
            if unit == "만":
                value *= 10000
            elif unit == "억":
                value *= 100000000
            op = FilterOperator.GTE if "이상" in vol_match.group(3) else FilterOperator.LTE
            filters.append(FilterCondition("volume", op, value))

        # Trading value conditions
        val_match = re.search(r'거래대금\s*(\d+)\s*(억|조)?\s*(이상|이하)', query_lower)
        if val_match:
            value = int(val_match.group(1))
            unit = val_match.group(2)
            if unit == "억":
                value *= 100000000
            elif unit == "조":
                value *= 1000000000000
            op = FilterOperator.GTE if "이상" in val_match.group(3) else FilterOperator.LTE
            filters.append(FilterCondition("trading_value", op, value))

        # Grade conditions
        if "a등급" in query_lower or "a등급 이상" in query_lower:
            filters.append(FilterCondition("total_grade", FilterOperator.IN, ["A+", "A"]))
        if "b등급 이상" in query_lower:
            filters.append(FilterCondition("total_grade", FilterOperator.IN, ["A+", "A", "B+", "B"]))

        # Golden/Dead cross
        if "골든크로스" in query_lower:
            filters.append(FilterCondition("macd", FilterOperator.GT, "macd_signal", table=None))
        if "데드크로스" in query_lower:
            filters.append(FilterCondition("macd", FilterOperator.LT, "macd_signal", table=None))

        return filters

    async def extract_with_llm(
        self,
        query: str,
        provider: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Extract query structure using LLM

        Args:
            query: User query
            provider: LLM provider
            model: Model name

        Returns:
            Extracted structure as dictionary
        """
        try:
            llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
            llm = get_llm(llm_provider, model_name=model)

            prompt = self.EXTRACTION_PROMPT.format(query=query)
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            # Parse JSON from response
            import json

            # Find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                logger.info(f"[SelfQueryRetriever] LLM extracted: {result}")
                return result

            return {}

        except Exception as e:
            logger.warning(f"[SelfQueryRetriever] LLM extraction failed: {e}")
            return {}

    async def extract(
        self,
        query: str,
        market: str = "KR",
        provider: str = None,
        model: str = None
    ) -> QueryStructure:
        """
        Extract full query structure

        Args:
            query: User query
            market: Market (KR/US)
            provider: LLM provider
            model: Model name

        Returns:
            QueryStructure object
        """
        # Rule-based extraction first
        filters = self._extract_filters_rule_based(query)
        sort = self._extract_sort(query)
        limit = self._extract_limit(query)

        # LLM extraction for additional details (if enabled)
        if self.use_llm:
            llm_result = await self.extract_with_llm(query, provider, model)

            # Merge LLM results
            if llm_result.get("limit") and not limit:
                limit = llm_result["limit"]

            if llm_result.get("sort_by") and not sort:
                sort_info = llm_result["sort_by"]
                sort = SortCondition(
                    column=sort_info.get("column", "trading_value"),
                    direction=sort_info.get("direction", "DESC")
                )

        # Determine required tables
        tables = self._infer_tables(filters, sort, market)

        # Determine required columns
        columns = self._infer_columns(filters, sort)

        structure = QueryStructure(
            filters=filters,
            sorts=[sort] if sort else [],
            limit=limit or 10,  # Default limit
            tables=tables,
            columns=columns
        )

        logger.info(f"[SelfQueryRetriever] Extracted: {len(filters)} filters, limit={limit}")
        return structure

    def _infer_tables(
        self,
        filters: List[FilterCondition],
        sort: Optional[SortCondition],
        market: str
    ) -> List[str]:
        """Infer required tables from conditions"""
        tables = set()
        prefix = "kr_" if market == "KR" else "us_"

        # Default table
        default_table = f"{prefix}intraday" if market == "KR" else f"{prefix}daily"
        tables.add(default_table)

        # Check filter columns
        indicator_cols = {"rsi", "macd", "macd_signal", "bb_upper", "bb_lower", "ma5", "ma20"}
        investor_cols = {"foreign_net_volume", "institution_net_volume"}
        grade_cols = {"total_grade", "total_score", "value_score"}

        all_cols = set()
        for f in filters:
            all_cols.add(f.column)
        if sort:
            all_cols.add(sort.column)

        if all_cols & indicator_cols:
            tables.add(f"{prefix}indicators")
        if all_cols & investor_cols and market == "KR":
            tables.add("kr_individual_investor_daily_trading")
        if all_cols & grade_cols:
            tables.add(f"{prefix}stock_grade")

        return list(tables)

    def _infer_columns(
        self,
        filters: List[FilterCondition],
        sort: Optional[SortCondition]
    ) -> List[str]:
        """Infer required columns"""
        columns = {"symbol", "stock_name", "close"}  # Default columns

        for f in filters:
            columns.add(f.column)

        if sort:
            columns.add(sort.column)

        return list(columns)

    def build_where_clause(self, filters: List[FilterCondition]) -> str:
        """Build SQL WHERE clause from filters"""
        if not filters:
            return ""

        conditions = [f.to_sql() for f in filters]
        return " AND ".join(conditions)

    def build_order_clause(self, sorts: List[SortCondition]) -> str:
        """Build SQL ORDER BY clause from sorts"""
        if not sorts:
            return ""

        return ", ".join(s.to_sql() for s in sorts)
