# services/chat/alpha_ai_model/tools/chart_data_formatter.py
"""
Chart Data Formatter

Converts SQL query results to chart-specific data formats
for frontend visualization libraries (Recharts, Lightweight Charts).

Supported formats:
- line_chart: Labels + datasets with data points
- bar_chart: Categories + values
- candlestick: OHLC data structure
- pie_chart: Labels + proportions
- table: Headers + rows (existing format)
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from config import logger


# Default chart colors
CHART_COLORS = [
    "#3b82f6",  # blue
    "#10b981",  # green
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#8b5cf6",  # purple
    "#ec4899",  # pink
    "#06b6d4",  # cyan
    "#84cc16",  # lime
    "#f97316",  # orange
    "#6366f1",  # indigo
]

# Date column names
DATE_COLUMNS = {"date", "time", "datetime", "timestamp", "trading_date", "trade_date"}

# OHLC column names
OHLC_COLUMNS = {"open", "high", "low", "close"}

# Column categories for smart line chart selection
PRICE_COLUMNS = {"close", "open", "high", "low", "adj_close", "current_price", "price"}
DEFAULT_PRICE_COLUMNS = {"close", "adj_close", "current_price", "price"}
INDICATOR_COLUMNS = {
    "rsi", "macd", "macd_signal", "macd_hist",
    "sma", "ema", "adx", "slowk", "slowd", "mfi",
    "real_upper_band", "real_middle_band", "real_lower_band",
    "vwap", "atr", "obv"
}

# Indicator groups for multi-chart display
# Groups related columns that share the same scale/meaning
INDICATOR_GROUPS = [
    {
        "key": "rsi",
        "label": "RSI",
        "columns": {"rsi"},
        "include_close": False,
    },
    {
        "key": "macd",
        "label": "MACD",
        "columns": {"macd", "macd_signal", "macd_hist"},
        "include_close": False,
    },
    {
        "key": "bollinger",
        "label": "볼린저밴드",
        "columns": {"real_upper_band", "real_middle_band", "real_lower_band"},
        "include_close": True,
    },
    {
        "key": "stochastic",
        "label": "스토캐스틱",
        "columns": {"slowk", "slowd"},
        "include_close": False,
    },
    {
        "key": "moving_avg",
        "label": "이동평균",
        "columns": {"sma", "ema"},
        "include_close": True,
    },
    {
        "key": "adx",
        "label": "ADX",
        "columns": {"adx"},
        "include_close": False,
    },
    {
        "key": "mfi",
        "label": "MFI",
        "columns": {"mfi"},
        "include_close": False,
    },
    {
        "key": "obv",
        "label": "OBV",
        "columns": {"obv"},
        "include_close": False,
    },
    {
        "key": "atr",
        "label": "ATR",
        "columns": {"atr"},
        "include_close": False,
    },
    {
        "key": "vwap",
        "label": "VWAP",
        "columns": {"vwap"},
        "include_close": True,
    },
    {
        "key": "quant_risk",
        "label": "리스크 지표",
        "columns": {"var_95", "sharpe_ratio", "volatility_annual", "beta", "max_drawdown_1y"},
        "include_close": False,
    },
    {
        "key": "quant_score",
        "label": "퀀트 스코어",
        "columns": {"final_score", "value_score", "quality_score", "momentum_score", "growth_score", "confidence_score"},
        "include_close": False,
    },
]
EXCLUDE_FROM_LINE_CHART = {
    "volume", "trading_value", "change_rate", "listed_shares",
    "market_cap", "symbol", "stock_name"
}

# Chart display labels (Korean)
CHART_COLUMN_LABELS = {
    "close": "종가", "open": "시가", "high": "고가", "low": "저가",
    "volume": "거래량", "trading_value": "거래대금",
    "change_rate": "등락률", "market_cap": "시가총액",
    "rsi": "RSI", "macd": "MACD", "macd_signal": "MACD시그널",
    "macd_hist": "MACD히스토그램", "sma": "이동평균(SMA)", "ema": "EMA",
    "adx": "ADX", "slowk": "스토캐스틱%K", "slowd": "스토캐스틱%D",
    "mfi": "MFI", "obv": "OBV", "atr": "ATR", "vwap": "VWAP",
    "real_upper_band": "볼린저상단", "real_middle_band": "볼린저중간",
    "real_lower_band": "볼린저하단",
    "adj_close": "수정종가", "current_price": "현재가",
    "var_95": "VaR(95%)", "sharpe_ratio": "샤프비율",
    "volatility_annual": "연간변동성", "beta": "베타",
    "max_drawdown_1y": "최대낙폭(1Y)",
    "final_score": "종합점수", "value_score": "가치점수",
    "quality_score": "퀄리티점수", "momentum_score": "모멘텀점수",
    "growth_score": "성장점수", "confidence_score": "신뢰도점수",
}

# Quant grade column names
QUANT_GRADE_COLUMNS = {"final_grade", "grade", "investment_grade", "quant_grade"}

# Quant grade to numeric score mapping
QUANT_GRADE_TO_SCORE = {
    "강력 매수": 3,
    "강력매수": 3,
    "매수": 2,
    "매수 고려": 1,
    "매수고려": 1,
    "중립": 0,
    "매도 고려": -1,
    "매도고려": -1,
    "매도": -2,
    "강력 매도": -3,
    "강력매도": -3,
}

# Y-axis tick labels for quant grade chart
QUANT_GRADE_Y_TICKS = {
    "3": "강력매수",
    "2": "매수",
    "1": "매수고려",
    "0": "중립",
    "-1": "매도고려",
    "-2": "매도",
    "-3": "강력매도",
}


class ChartDataFormatter:
    """
    Formats SQL results to chart-compatible data structures.
    """

    def format(
        self,
        chart_type: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str = "",
        market: str = "KR",
        indicators: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Format data for the specified chart type.

        Args:
            chart_type: Type of chart
            columns: Column names from SQL result
            data: SQL result rows
            title: Chart title
            market: Market type for currency formatting (KR/US)
            indicators: Extracted indicator names from entity_extractor (optional)

        Returns:
            Visualization data dict or None
        """
        if not data:
            return None

        # Multi-indicator chart (from visualization_resolver multi_chart decision)
        if chart_type == "multi_chart":
            try:
                return self._format_multi_indicator_chart(columns, data, title, market, indicators)
            except Exception as e:
                logger.error(f"[ChartDataFormatter] Error formatting multi_chart: {e}")
                return self._format_table(columns, data, title, market)

        # Special handling for quant grade time series data
        if self._is_quant_grade_data(columns, data):
            logger.info("[ChartDataFormatter] Detected quant grade data, using special formatter")
            try:
                return self._format_quant_grade_chart(columns, data, title, market)
            except Exception as e:
                logger.error(f"[ChartDataFormatter] Error formatting quant grade chart: {e}")
                return self._format_table(columns, data, title, market)

        formatter_map = {
            "line_chart": self._format_line_chart,
            "bar_chart": self._format_bar_chart,
            "candlestick": self._format_candlestick,
            "pie_chart": self._format_pie_chart,
            "table": self._format_table,
        }

        formatter = formatter_map.get(chart_type)
        if not formatter:
            logger.warning(f"[ChartDataFormatter] Unknown chart type: {chart_type}")
            return self._format_table(columns, data, title, market)

        try:
            return formatter(columns, data, title, market)
        except Exception as e:
            logger.error(f"[ChartDataFormatter] Error formatting {chart_type}: {e}")
            return self._format_table(columns, data, title, market)

    def _serialize_value(self, val: Any) -> Any:
        """Convert value to JSON-serializable format."""
        if val is None:
            return None
        if isinstance(val, Decimal):
            return float(val)
        if isinstance(val, (date, datetime)):
            return val.isoformat() if isinstance(val, datetime) else str(val)
        if isinstance(val, (int, float)):
            return val
        return str(val)

    def _find_date_column(self, columns: List[str]) -> Optional[str]:
        """Find date column from column list."""
        for col in columns:
            if col.lower() in DATE_COLUMNS:
                return col
        return None

    def _find_numeric_columns(self, columns: List[str], exclude: set = None) -> List[str]:
        """Find numeric columns (excluding specified ones)."""
        exclude = exclude or set()
        return [c for c in columns if c.lower() not in exclude and c.lower() not in DATE_COLUMNS]

    def _format_date_label(self, val: Any) -> str:
        """Format date value for chart label."""
        if isinstance(val, datetime):
            return val.strftime("%m/%d")
        if isinstance(val, date):
            return val.strftime("%m/%d")
        if isinstance(val, str) and len(val) >= 10:
            # Parse YYYY-MM-DD format
            try:
                return val[5:10].replace("-", "/")
            except Exception:
                pass
        return str(val)

    def _format_date_raw(self, val: Any) -> str:
        """Format date value as YYYY-MM-DD for lightweight-charts Time type."""
        if isinstance(val, datetime):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, date):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, str) and len(val) >= 10:
            return val[:10]
        return str(val)

    def _find_quant_grade_column(self, columns: List[str]) -> Optional[str]:
        """Find quant grade column from column list."""
        for col in columns:
            if col.lower() in QUANT_GRADE_COLUMNS:
                return col
        return None

    def _is_quant_grade_data(
        self,
        columns: List[str],
        data: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if data contains quant grade time series.

        Requirements:
        - Has a date column
        - Has a quant grade column (final_grade, grade, etc.)
        - Grade values are in QUANT_GRADE_TO_SCORE mapping
        - Multiple rows (time series)
        """
        if not columns or not data or len(data) < 2:
            return False

        col_lower = {c.lower() for c in columns}

        # Must have date column
        has_date = bool(DATE_COLUMNS & col_lower)
        if not has_date:
            return False

        # Must have grade column
        grade_col = self._find_quant_grade_column(columns)
        if not grade_col:
            return False

        # Check if grade values are valid quant grades
        first_grade = data[0].get(grade_col, "")
        if first_grade not in QUANT_GRADE_TO_SCORE:
            return False

        logger.debug(f"[ChartDataFormatter] Quant grade detected: col={grade_col}, first_value={first_grade}")
        return True

    def _format_quant_grade_chart(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Format quant grade data as line chart with numeric conversion.

        Converts text grades to numeric scores:
        - 강력매수: 3, 매수: 2, 매수고려: 1
        - 중립: 0
        - 매도고려: -1, 매도: -2, 강력매도: -3

        Expected output structure:
        {
            "type": "line_chart",
            "title": "...",
            "data": {
                "labels": ["01/01", "01/02", ...],
                "datasets": [{"label": "투자등급", "data": [2, 2, 1, 0, ...]}]
            },
            "options": {
                "xAxisLabel": "날짜",
                "yAxisLabel": "투자등급",
                "yAxisMin": -3,
                "yAxisMax": 3,
                "yAxisTicks": {"3": "강력매수", "2": "매수", ...}
            }
        }
        """
        date_col = self._find_date_column(columns)
        grade_col = self._find_quant_grade_column(columns)

        # Sort by date ascending for proper time series display
        sorted_data = sorted(
            data,
            key=lambda x: x.get(date_col) or "",
            reverse=False
        )

        # Build labels (dates)
        labels = [self._format_date_label(row.get(date_col)) for row in sorted_data]

        # Convert grades to numeric scores
        scores = []
        for row in sorted_data:
            grade = row.get(grade_col, "")
            score = QUANT_GRADE_TO_SCORE.get(grade, 0)
            scores.append(score)

        # Determine color based on latest grade trend
        latest_score = scores[-1] if scores else 0
        if latest_score >= 2:
            color = "#ef4444"  # red for buy signal
        elif latest_score <= -2:
            color = "#3b82f6"  # blue for sell signal
        else:
            color = "#6b7280"  # gray for neutral

        return {
            "type": "line_chart",
            "title": title or "투자등급 추이",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "투자등급",
                    "data": scores,
                    "borderColor": color,
                    "backgroundColor": color + "20",
                    "tension": 0.1,  # slight curve for readability
                }]
            },
            "options": {
                "xAxisLabel": "날짜",
                "yAxisLabel": "투자등급",
                "yAxisMin": -3,
                "yAxisMax": 3,
                "yAxisTicks": QUANT_GRADE_Y_TICKS,
                "isQuantGrade": True,  # flag for frontend special handling
            }
        }

    def _build_single_line_chart(self, labels, cols, data, title, label_col):
        """Build a single line_chart visualization object."""
        datasets = []
        for idx, col in enumerate(cols):
            color = CHART_COLORS[idx % len(CHART_COLORS)]
            datasets.append({
                "label": CHART_COLUMN_LABELS.get(col.lower(), col),
                "data": [self._serialize_value(row.get(col)) for row in data],
                "borderColor": color,
                "backgroundColor": color + "20",
            })

        return {
            "type": "line_chart",
            "title": title,
            "data": {"labels": labels, "datasets": datasets},
            "options": {
                "xAxisLabel": label_col,
                "yAxisLabel": CHART_COLUMN_LABELS.get(cols[0].lower(), cols[0]) if cols else "",
            }
        }

    def _format_multi_chart(self, columns, data, title, market, date_col, label_col, labels, matched_groups, close_col):
        """Build multi_chart with individual charts per indicator group."""
        charts = []

        # 1) Close price chart (always first)
        if close_col:
            charts.append({
                "label": CHART_COLUMN_LABELS.get(close_col.lower(), close_col),
                "visualization": self._build_single_line_chart(
                    labels=labels,
                    cols=[close_col],
                    data=data,
                    title=title,
                    label_col=label_col,
                )
            })

        # 2) Per-indicator-group charts
        for group in matched_groups:
            group_cols = [c for c in columns if c.lower() in group["columns"]]
            if not group_cols:
                continue

            chart_cols = group_cols
            if group["include_close"] and close_col:
                chart_cols = [close_col] + group_cols

            charts.append({
                "label": group["label"],
                "visualization": self._build_single_line_chart(
                    labels=labels,
                    cols=chart_cols,
                    data=data,
                    title=f"{title} - {group['label']}",
                    label_col=label_col,
                )
            })

        return {
            "type": "multi_chart",
            "title": title,
            "data": {
                "charts": charts,
                "defaultIndex": 0,
            },
        }

    def _format_multi_indicator_chart(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str,
        market: str,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Format multi-indicator comparison data as individual sub-charts.

        Handles two data shapes:
        - Snapshot: one row per stock (X=stock name, Y=indicator value) -> bar_chart sub-charts
        - Time series: multiple rows with date column (X=date, Y=indicator value) -> line_chart sub-charts

        Args:
            columns: Column names from SQL result
            data: SQL result rows
            title: Chart title
            market: Market type
            indicators: Extracted indicator names (e.g. ["macd", "rsi"])

        Returns:
            multi_chart visualization dict
        """
        col_lower_map = {c.lower(): c for c in columns}
        col_lower_set = set(col_lower_map.keys())

        # 1. Match requested indicators to actual columns via INDICATOR_GROUPS
        matched_groups = []
        if indicators:
            for ind in indicators:
                ind_l = ind.lower()
                for group in INDICATOR_GROUPS:
                    if ind_l == group["key"] or ind_l in group["columns"]:
                        if group not in matched_groups:
                            # Check at least one group column exists in data
                            if group["columns"] & col_lower_set:
                                matched_groups.append(group)
                        break

        # Fallback: if no groups matched via indicators, scan columns directly
        if len(matched_groups) < 2:
            matched_groups = [
                g for g in INDICATOR_GROUPS
                if g["columns"] & col_lower_set
            ]

        if not matched_groups:
            logger.warning("[ChartDataFormatter] multi_chart: no indicator groups matched, falling back to table")
            return self._format_table(columns, data, title, market)

        # 2. Detect data shape: snapshot vs time series
        date_col = self._find_date_column(columns)
        label_candidates = ["stock_name", "company_name", "symbol", "name"]
        label_col = None
        for cand in label_candidates:
            if cand in col_lower_set:
                label_col = col_lower_map[cand]
                break

        is_time_series = date_col is not None and len(data) > 1

        # Detect multi-entity time series (e.g., multiple stocks)
        unique_entities = []
        entity_date_map = {}
        if is_time_series and label_col and label_col.lower() not in DATE_COLUMNS:
            seen = {}
            for row in data:
                ent = str(row.get(label_col, ""))
                if ent and ent not in seen:
                    seen[ent] = True
                    unique_entities.append(ent)
                # Build (entity, date) -> row lookup for O(1) access
                d = row.get(date_col)
                if ent and d:
                    entity_date_map[(ent, d)] = row

        has_multiple_entities = len(unique_entities) > 1

        # Build common sorted date axis for multi-entity
        unique_dates = []
        if has_multiple_entities:
            date_set = set()
            for row in data:
                d = row.get(date_col)
                if d is not None and d not in date_set:
                    date_set.add(d)
            unique_dates = sorted(date_set)
            logger.info(
                f"[ChartDataFormatter] Multi-entity detected: "
                f"{len(unique_entities)} entities, {len(unique_dates)} dates"
            )

        # For snapshot: check if we have label column and rows represent different stocks
        is_snapshot = (not is_time_series) and label_col is not None

        # If neither detected, try heuristic: few rows + label col = snapshot
        if not is_time_series and not is_snapshot and label_col:
            is_snapshot = True
        if not is_time_series and not is_snapshot and not label_col:
            # No label column, no date -> use first column as label
            label_col = columns[0]
            is_snapshot = True

        # 3. Build sub-charts per indicator group
        charts = []
        for group in matched_groups:
            group_cols = [col_lower_map[c] for c in group["columns"] if c in col_lower_set]
            if not group_cols:
                continue

            if is_time_series and has_multiple_entities:
                # Multi-entity time series: one dataset per entity per column
                labels = [self._format_date_label(d) for d in unique_dates]
                datasets = []
                color_idx = 0
                for col in group_cols:
                    for entity in unique_entities:
                        color = CHART_COLORS[color_idx % len(CHART_COLORS)]
                        color_idx += 1
                        values = [
                            self._serialize_value(
                                entity_date_map.get((entity, d), {}).get(col)
                            )
                            for d in unique_dates
                        ]
                        col_label = CHART_COLUMN_LABELS.get(col.lower(), col)
                        # Single-column group: label = entity name only
                        # Multi-column group: label = "entity column_name"
                        if len(group_cols) == 1:
                            ds_label = entity
                        else:
                            ds_label = f"{entity} {col_label}"
                        datasets.append({
                            "label": ds_label,
                            "data": values,
                            "borderColor": color,
                            "backgroundColor": color + "20",
                        })
                sub_viz = {
                    "type": "line_chart",
                    "title": f"{title} - {group['label']}",
                    "data": {"labels": labels, "datasets": datasets},
                    "options": {
                        "xAxisLabel": date_col,
                        "yAxisLabel": group["label"],
                    },
                }
            elif is_time_series:
                # Single entity time series: line_chart per group
                labels = [self._format_date_label(row.get(date_col)) for row in data]
                datasets = []
                for idx, col in enumerate(group_cols):
                    color = CHART_COLORS[idx % len(CHART_COLORS)]
                    datasets.append({
                        "label": CHART_COLUMN_LABELS.get(col.lower(), col),
                        "data": [self._serialize_value(row.get(col)) for row in data],
                        "borderColor": color,
                        "backgroundColor": color + "20",
                    })
                sub_viz = {
                    "type": "line_chart",
                    "title": f"{title} - {group['label']}",
                    "data": {"labels": labels, "datasets": datasets},
                    "options": {
                        "xAxisLabel": date_col,
                        "yAxisLabel": group["label"],
                    },
                }
            else:
                # Snapshot: bar_chart per group (one bar per stock, one chart per indicator column)
                labels = [str(row.get(label_col, "")) for row in data]
                # For bar chart, use first column of the group
                for col in group_cols:
                    values = [self._serialize_value(row.get(col)) for row in data]
                    colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(data))]
                    sub_viz = {
                        "type": "bar_chart",
                        "title": f"{title} - {CHART_COLUMN_LABELS.get(col.lower(), col)}",
                        "data": {
                            "labels": labels,
                            "datasets": [{
                                "label": CHART_COLUMN_LABELS.get(col.lower(), col),
                                "data": values,
                                "backgroundColor": colors,
                            }],
                        },
                        "options": {
                            "xAxisLabel": label_col,
                            "yAxisLabel": CHART_COLUMN_LABELS.get(col.lower(), col),
                        },
                    }
                    charts.append({
                        "label": CHART_COLUMN_LABELS.get(col.lower(), col),
                        "visualization": sub_viz,
                    })
                continue  # skip the append below since snapshot appends per-column

            charts.append({
                "label": group["label"],
                "visualization": sub_viz,
            })

        if not charts:
            logger.warning("[ChartDataFormatter] multi_chart: no charts built, falling back to table")
            return self._format_table(columns, data, title, market)

        logger.info(f"[ChartDataFormatter] multi_chart built: {len(charts)} sub-charts")
        return {
            "type": "multi_chart",
            "title": title,
            "data": {
                "charts": charts,
                "defaultIndex": 0,
            },
        }

    def _format_line_chart(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Format data for line chart.

        Expected structure:
        {
            "type": "line_chart",
            "title": "...",
            "data": {
                "labels": ["01/01", "01/02", ...],
                "datasets": [{"label": "...", "data": [...], "borderColor": "..."}]
            },
            "options": {"xAxisLabel": "...", "yAxisLabel": "..."}
        }
        """
        date_col = self._find_date_column(columns)
        value_cols = self._find_numeric_columns(columns, {date_col} if date_col else set())

        # Use first column as label if no date column
        label_col = date_col or columns[0]
        if not value_cols:
            value_cols = [c for c in columns if c != label_col][:3]

        # Build labels first (needed by both single and multi chart paths)
        labels = []
        for row in data:
            val = row.get(label_col)
            if date_col:
                labels.append(self._format_date_label(val))
            else:
                labels.append(str(val) if val else "")

        # Smart column selection for line chart
        value_cols_lower = {c: c.lower() for c in value_cols}
        indicators = [c for c in value_cols if value_cols_lower[c] in INDICATOR_COLUMNS]
        default_prices = [c for c in value_cols if value_cols_lower[c] in DEFAULT_PRICE_COLUMNS]
        filtered = [c for c in value_cols if value_cols_lower[c] not in EXCLUDE_FROM_LINE_CHART]

        # Check for multiple indicator groups -> multi_chart
        value_cols_lower_set = {c.lower() for c in value_cols}
        matched_groups = [
            g for g in INDICATOR_GROUPS
            if g["columns"] & value_cols_lower_set
        ]
        close_col = next((c for c in value_cols if c.lower() in DEFAULT_PRICE_COLUMNS), None)

        if len(matched_groups) >= 2:
            return self._format_multi_chart(
                columns=columns, data=data, title=title, market=market,
                date_col=date_col, label_col=label_col, labels=labels,
                matched_groups=matched_groups, close_col=close_col
            )

        # Single chart path
        if indicators:
            selected_cols = indicators[:3]
        elif default_prices:
            selected_cols = default_prices[:1]
        elif filtered:
            selected_cols = filtered[:3]
        else:
            selected_cols = value_cols[:3]

        return self._build_single_line_chart(
            labels=labels,
            cols=selected_cols,
            data=data,
            title=title,
            label_col=label_col,
        )

    def _format_bar_chart(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Format data for bar chart.

        Expected structure:
        {
            "type": "bar_chart",
            "title": "...",
            "data": {
                "labels": ["A", "B", "C", ...],
                "datasets": [{"label": "...", "data": [...], "backgroundColor": [...]}]
            },
            "options": {"xAxisLabel": "...", "yAxisLabel": "..."}
        }
        """
        # First column as labels, second as values
        label_col = columns[0]
        value_col = columns[1] if len(columns) > 1 else columns[0]

        labels = [str(row.get(label_col, "")) for row in data]
        values = [self._serialize_value(row.get(value_col)) for row in data]

        # Assign colors
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(data))]

        return {
            "type": "bar_chart",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": CHART_COLUMN_LABELS.get(value_col.lower(), value_col),
                    "data": values,
                    "backgroundColor": colors,
                }]
            },
            "options": {
                "xAxisLabel": label_col,
                "yAxisLabel": CHART_COLUMN_LABELS.get(value_col.lower(), value_col),
            }
        }

    def _format_candlestick(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Format data for candlestick chart.

        Expected structure:
        {
            "type": "candlestick",
            "title": "...",
            "data": {
                "labels": ["01/01", "01/02", ...],
                "datasets": [{
                    "data": [
                        {"open": 100, "high": 110, "low": 95, "close": 105},
                        ...
                    ]
                }]
            },
            "options": {"xAxisLabel": "...", "yAxisLabel": "..."}
        }
        """
        date_col = self._find_date_column(columns)
        label_col = date_col or columns[0]

        # Build labels (YYYY-MM-DD format required by lightweight-charts)
        labels = []
        for row in data:
            val = row.get(label_col)
            labels.append(self._format_date_raw(val))

        # Safety net: duplicate timestamps cause lightweight-charts to crash
        if len(set(labels)) < len(labels):
            logger.warning(
                f"[ChartDataFormatter] Candlestick has duplicate dates "
                f"({len(labels)} labels, {len(set(labels))} unique), falling back to table"
            )
            return self._format_table(columns, data, title, market)

        # Build OHLC data
        # Find OHLC columns (case-insensitive)
        col_map = {c.lower(): c for c in columns}

        candle_data = []
        for row in data:
            candle = {
                "open": self._serialize_value(row.get(col_map.get("open"))),
                "high": self._serialize_value(row.get(col_map.get("high"))),
                "low": self._serialize_value(row.get(col_map.get("low"))),
                "close": self._serialize_value(row.get(col_map.get("close"))),
            }
            candle_data.append(candle)

        currency = "$" if market == "US" else "won"

        return {
            "type": "candlestick",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": [{"data": candle_data}]
            },
            "options": {
                "xAxisLabel": "date",
                "yAxisLabel": f"price ({currency})",
            }
        }

    def _format_pie_chart(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Format data for pie chart.

        Expected structure:
        {
            "type": "pie_chart",
            "title": "...",
            "data": {
                "labels": ["A", "B", "C", ...],
                "datasets": [{"data": [30, 50, 20], "backgroundColor": [...]}]
            },
            "options": {"showPercentage": true}
        }
        """
        # First column as labels, second as values
        label_col = columns[0]
        value_col = columns[1] if len(columns) > 1 else columns[0]

        labels = [str(row.get(label_col, "")) for row in data]
        values = [self._serialize_value(row.get(value_col)) for row in data]

        # Assign colors
        colors = [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(data))]

        return {
            "type": "pie_chart",
            "title": title,
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": colors,
                }]
            },
            "options": {
                "showPercentage": True,
            }
        }

    def _format_table(
        self,
        columns: List[str],
        data: List[Dict[str, Any]],
        title: str,
        market: str
    ) -> Dict[str, Any]:
        """
        Format data for table (fallback format).

        Expected structure:
        {
            "type": "table",
            "title": "...",
            "data": {
                "headers": ["col1", "col2", ...],
                "rows": [[val1, val2, ...], ...],
                "total_count": 100,
                "displayed_count": 50
            },
            "options": {"sortable": true, "pagination": false}
        }
        """
        rows = []
        for row in data:
            row_data = [self._serialize_value(row.get(col)) for col in columns]
            rows.append(row_data)

        return {
            "type": "table",
            "title": title,
            "data": {
                "headers": [CHART_COLUMN_LABELS.get(c.lower(), c) for c in columns],
                "rows": rows,
                "total_count": len(data),
                "displayed_count": len(rows),
            },
            "options": {
                "sortable": True,
                "pagination": len(rows) > 20,
            }
        }


# Singleton instance
chart_data_formatter = ChartDataFormatter()
