# services/chat/alpha_ai_model/graph/nodes/visualization_resolver.py
"""
Visualization Type Resolver (Hybrid Approach)

Determines the appropriate chart type based on:
1. Keyword matching from user question
2. Data structure analysis from SQL results
3. Default fallback to table

Supported chart types:
- line_chart: Time series, price trends
- bar_chart: Category comparisons
- candlestick: OHLC price charts
- pie_chart: Proportions, distributions
- table: Default for complex data
"""

from typing import List, Dict, Any, Optional
from config import logger


# =============================================================================
# KEYWORD TO CHART TYPE MAPPING
# =============================================================================

KEYWORD_TO_CHART = {
    # line_chart - Time series, trends
    "추이": "line_chart",
    "흐름": "line_chart",
    "변화": "line_chart",
    "추세": "line_chart",
    "동향": "line_chart",
    "이력": "line_chart",
    "히스토리": "line_chart",
    "history": "line_chart",
    "trend": "line_chart",

    # Explicit graph/chart request - default to line_chart
    "그래프": "line_chart",
    "그래프로": "line_chart",
    "차트로": "line_chart",
    "graph": "line_chart",
    "chart": "line_chart",
    "시각화": "line_chart",
    "visualize": "line_chart",

    # candlestick - OHLC charts
    "일봉": "candlestick",
    "주봉": "candlestick",
    "월봉": "candlestick",
    "캔들": "candlestick",
    "봉차트": "candlestick",
    "candlestick": "candlestick",
    "ohlc": "candlestick",

    # bar_chart - Comparisons
    "비교": "bar_chart",

    "vs": "bar_chart",
    "차이": "bar_chart",
    "compare": "bar_chart",
    "막대그래프": "bar_chart",
    "막대차트": "bar_chart",
    "bar graph": "bar_chart",

    # pie_chart - Proportions
    "비중": "pie_chart",
    "비율": "pie_chart",
    "구성": "pie_chart",
    "분포": "pie_chart",
    "점유율": "pie_chart",
    "포트폴리오": "pie_chart",
    "proportion": "pie_chart",
    "distribution": "pie_chart",
    "원그래프": "pie_chart",
    "파이차트": "pie_chart",

    # table - Lists, rankings
    "상위": "table",
    "하위": "table",
    "랭킹": "table",
    "목록": "table",
    "리스트": "table",
    "순위": "table",
    "top": "table",
    "bottom": "table",
    "list": "table",
}

# Columns that indicate date/time data
DATE_COLUMNS = {"date", "time", "datetime", "timestamp", "trading_date", "trade_date"}

# Columns that indicate OHLC data
OHLC_COLUMNS = {"open", "high", "low", "close"}

# Columns that indicate price data (for line chart default)
PRICE_COLUMNS = {"close", "price", "current_price", "adj_close"}

# Columns that identify different entities (stocks)
ENTITY_COLUMNS = {"stock_name", "name", "symbol", "ticker"}


class VisualizationResolver:
    """
    Determines visualization type using hybrid approach:
    1. Keyword matching
    2. Data structure analysis
    3. Default fallback
    """

    def resolve(
        self,
        question: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        intent: Optional[str] = None,
        indicators: Optional[List[str]] = None
    ) -> str:
        """
        Determine the best visualization type.

        Args:
            question: User's original question
            columns: Column names from SQL result
            data: SQL result data rows
            intent: Detected intent (optional)
            indicators: Extracted indicator names from entity_extractor (optional)

        Returns:
            Chart type string: 'line_chart', 'bar_chart', 'candlestick', 'pie_chart', 'multi_chart', 'table'
        """
        # Step 0: Multi-indicator detection (priority over keyword matching)
        if indicators and len(indicators) >= 2:
            col_names = {c.lower() for c in columns}
            matched = [
                ind for ind in indicators
                if ind.lower() in col_names or any(ind.lower() in c for c in col_names)
            ]
            if len(matched) >= 2:
                logger.info(f"[VisualizationResolver] Multi-indicator detected: {matched} -> 'multi_chart'")
                return "multi_chart"

        # Step 0-1: Auto-detect indicators for analysis intent
        if intent == "analysis" and (not indicators or len(indicators) < 2):
            col_names = {c.lower() for c in columns}
            _INDICATOR_COLUMNS = {
                "rsi", "macd", "macd_signal", "macd_hist",
                "real_upper_band", "real_middle_band", "real_lower_band",
                "sma", "ema", "atr", "slowk", "slowd", "adx", "obv", "vwap",
            }
            auto_detected = col_names & _INDICATOR_COLUMNS
            if len(auto_detected) >= 2:
                logger.info(f"[VisualizationResolver] Analysis auto-detect: {len(auto_detected)} indicators -> 'multi_chart'")
                return "multi_chart"

        # Step 1: Keyword matching
        chart_type = self._match_keyword(question)
        if chart_type:
            logger.info(f"[VisualizationResolver] Keyword match: '{chart_type}'")
        else:
            # Step 2: Data structure analysis
            chart_type = self._analyze_structure(columns, data)
            if chart_type:
                logger.info(f"[VisualizationResolver] Structure analysis: '{chart_type}'")
            else:
                # Step 3: Default fallback
                chart_type = "table"
                logger.info("[VisualizationResolver] Default fallback: 'table'")

        # Post-validation: candlestick requires single-entity time series
        if chart_type == "candlestick":
            chart_type = self._validate_candlestick(columns, data, chart_type)

        return chart_type

    def _match_keyword(self, question: str) -> Optional[str]:
        """
        Match keywords in question to chart types using scoring.
        Counts all keyword matches per chart type and returns the type
        with the most matches. Ties are broken by priority (table first).

        Args:
            question: User's question

        Returns:
            Chart type or None if no match
        """
        question_lower = question.lower()
        priority = ["table", "line_chart", "candlestick", "bar_chart", "pie_chart"]

        scores: Dict[str, int] = {}
        for keyword, chart_type in KEYWORD_TO_CHART.items():
            if keyword in question_lower:
                scores[chart_type] = scores.get(chart_type, 0) + 1

        if not scores:
            return None

        return max(scores, key=lambda t: (scores[t], -priority.index(t)))

    def _analyze_structure(
        self,
        columns: List[str],
        data: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Analyze data structure to determine chart type.

        Args:
            columns: Column names
            data: Data rows

        Returns:
            Chart type or None if unclear
        """
        if not columns or not data:
            return None

        column_lower = {c.lower() for c in columns}
        row_count = len(data)
        col_count = len(columns)

        # Check for OHLC pattern -> candlestick
        if OHLC_COLUMNS.issubset(column_lower):
            return "candlestick"

        # Check for time series pattern -> line_chart
        has_date = bool(DATE_COLUMNS & column_lower)
        has_price = bool(PRICE_COLUMNS & column_lower)

        # Date + price columns with sufficient data -> line_chart (stock price analysis)
        if has_date and has_price and row_count >= 5:
            return "line_chart"

        # Date column with few columns -> line_chart (general time series)
        if has_date and col_count <= 4 and row_count >= 5:
            return "line_chart"

        # Check for proportion pattern -> pie_chart
        # Small number of rows with 2 columns (label + value)
        if row_count <= 6 and col_count == 2:
            # Check if second column is numeric
            first_row = data[0]
            values = list(first_row.values())
            if len(values) >= 2 and isinstance(values[1], (int, float)):
                return "pie_chart"

        # Check for comparison pattern -> bar_chart
        # Medium number of rows with 2 columns
        if 2 <= row_count <= 15 and col_count == 2:
            return "bar_chart"

        # Default: no clear pattern
        return None

    def _validate_candlestick(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        original_type: str
    ) -> str:
        """
        Validate candlestick is appropriate for the data.
        Candlestick requires single-entity time series with sufficient data points.
        Multi-stock data causes duplicate timestamps in lightweight-charts.

        Returns:
            'candlestick' if valid, alternative chart type otherwise
        """
        entity_col = self._find_entity_column(columns)
        if entity_col:
            unique_entities = {row.get(entity_col) for row in data if row.get(entity_col)}
            if len(unique_entities) > 1:
                logger.info(
                    f"[VisualizationResolver] Candlestick rejected: "
                    f"{len(unique_entities)} entities detected -> 'line_chart'"
                )
                return "line_chart"

        if len(data) < 5:
            logger.info(
                f"[VisualizationResolver] Candlestick rejected: "
                f"only {len(data)} rows (min 5) -> 'bar_chart'"
            )
            return "bar_chart"

        return "candlestick"

    def _find_entity_column(self, columns: List[str]) -> Optional[str]:
        """Find column that identifies different entities (stocks)."""
        for col in columns:
            if col.lower() in ENTITY_COLUMNS:
                return col
        return None

    def should_visualize(
        self,
        data: List[Dict[str, Any]],
        chart_type: str
    ) -> bool:
        """
        Check if visualization should be generated.

        Args:
            data: SQL result data
            chart_type: Determined chart type

        Returns:
            True if visualization should be generated
        """
        if not data:
            return False

        row_count = len(data)

        # Minimum data requirements per chart type
        min_rows = {
            "line_chart": 2,
            "candlestick": 2,
            "bar_chart": 2,
            "pie_chart": 2,
            "multi_chart": 1,
            "table": 1,
        }

        return row_count >= min_rows.get(chart_type, 1)


# Singleton instance
visualization_resolver = VisualizationResolver()
