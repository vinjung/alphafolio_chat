# services/chat/alpha_ai_model/tools/supplementary_chart_builder.py
"""
Supplementary Chart Builder

Builds post-query technical indicator charts from fixed-pattern SQL queries.
Uses the top-1 few-shot example's chart_indicators flag to decide whether
to generate supplementary charts. Does not modify the main SQL pipeline.
"""
from typing import List, Dict, Any, Optional, Set
from config import logger
from database import db


# ---------------------------------------------------------------------------
# Indicator column sets
# ---------------------------------------------------------------------------

SINGLE_STOCK_COLUMNS = [
    "close", "rsi", "macd", "macd_signal", "macd_hist",
    "real_upper_band", "real_middle_band", "real_lower_band",
    "adx", "mfi", "slowk", "slowd", "sma", "ema",
]

MULTI_STOCK_COLUMNS = [
    "close", "rsi", "adx", "mfi", "slowk", "slowd",
]

# Chart tab definitions: (label, column_keys, chart_type)
SINGLE_TABS = [
    ("Close", ["close"]),
    ("RSI", ["rsi"]),
    ("MACD", ["macd", "macd_signal", "macd_hist"]),
    ("Bollinger", ["close", "real_upper_band", "real_middle_band", "real_lower_band"]),
    ("ADX", ["adx"]),
    ("MFI", ["mfi"]),
    ("Stochastic", ["slowk", "slowd"]),
    ("SMA/EMA", ["close", "sma", "ema"]),
]

MULTI_TABS = [
    ("Close", ["close"]),
    ("RSI", ["rsi"]),
    ("ADX", ["adx"]),
    ("MFI", ["mfi"]),
    ("Stochastic", ["slowk", "slowd"]),
]

# Column display names for chart labels
COLUMN_LABELS = {
    "close": "Close",
    "rsi": "RSI",
    "macd": "MACD",
    "macd_signal": "Signal",
    "macd_hist": "Histogram",
    "real_upper_band": "Upper Band",
    "real_middle_band": "Middle Band",
    "real_lower_band": "Lower Band",
    "adx": "ADX",
    "mfi": "MFI",
    "slowk": "Slow %K",
    "slowd": "Slow %D",
    "sma": "SMA",
    "ema": "EMA",
}

CHART_COLORS = [
    "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
    "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1",
]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def build_supplementary_charts(
    query_result: List[Dict],
    few_shot_examples: List[Dict],
    market: str
) -> Optional[Dict[str, Any]]:
    """Build supplementary technical indicator charts from query results.

    Checks the top-1 few-shot example's chart_indicators flag. If True,
    extracts symbols from query_result, fetches 60-day indicator history,
    and returns a multi_chart structure.

    Args:
        query_result: Main SQL query result rows
        few_shot_examples: Retrieved few-shot examples (top-1 used)
        market: Market identifier ("KR", "US", "BOTH")

    Returns:
        multi_chart dict or None if not applicable
    """
    if not query_result or not few_shot_examples:
        return None

    # Check top-1 example's chart_indicators flag
    top_example = few_shot_examples[0]
    if not top_example.get("chart_indicators", False):
        return None

    # Extract symbols from query result
    symbols = _extract_symbols(query_result)
    if not symbols:
        return None

    logger.info(
        f"[SupplementaryChart] Building charts for {len(symbols)} symbols, market={market}"
    )

    try:
        # Determine per-row market if BOTH
        market_map = _build_market_map(query_result, market)

        # Select top 5 by market cap
        selected = await _select_top_symbols(symbols, market_map)
        if not selected:
            return None

        # Determine single vs multi mode
        is_single = len(selected) == 1

        # Fetch 60-day indicator data
        rows = await _fetch_indicator_data(selected, market_map, is_single)
        if not rows:
            return None

        # Build multi_chart
        chart = _build_chart(rows, selected, market_map, is_single)
        return chart

    except Exception as e:
        logger.error(f"[SupplementaryChart] Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Symbol extraction
# ---------------------------------------------------------------------------

def _extract_symbols(query_result: List[Dict]) -> List[str]:
    """Extract unique symbol values from query result rows."""
    symbols = []
    seen: Set[str] = set()
    for row in query_result:
        sym = row.get("symbol")
        if sym and sym not in seen:
            symbols.append(sym)
            seen.add(sym)
    return symbols


def _build_market_map(query_result: List[Dict], default_market: str) -> Dict[str, str]:
    """Build symbol -> market mapping from result rows.

    If rows have a 'market' column, use it. Otherwise default to the given market.
    For BOTH market with no per-row market column, infer from symbol format.
    """
    market_map: Dict[str, str] = {}
    for row in query_result:
        sym = row.get("symbol")
        if not sym:
            continue
        row_market = row.get("market")
        if row_market:
            market_map[sym] = row_market.upper()
        elif default_market == "BOTH":
            # Heuristic: KR symbols are numeric, US symbols are alphabetic
            market_map[sym] = "KR" if sym.isdigit() else "US"
        else:
            market_map[sym] = default_market
    return market_map


# ---------------------------------------------------------------------------
# Top-N selection by market cap
# ---------------------------------------------------------------------------

async def _select_top_symbols(
    symbols: List[str],
    market_map: Dict[str, str],
    limit: int = 5
) -> List[str]:
    """Select top N symbols by market cap using dedicated queries."""
    if len(symbols) <= limit:
        return symbols

    try:
        kr_syms = [s for s in symbols if market_map.get(s) == "KR"]
        us_syms = [s for s in symbols if market_map.get(s) == "US"]

        ranked: List[tuple] = []  # (symbol, market_cap)

        async with db.pool.acquire() as conn:
            if kr_syms:
                placeholders = ", ".join(f"${i+1}" for i in range(len(kr_syms)))
                rows = await conn.fetch(
                    f"SELECT symbol, market_cap FROM kr_intraday "
                    f"WHERE symbol IN ({placeholders}) "
                    f"ORDER BY market_cap DESC NULLS LAST",
                    *kr_syms
                )
                ranked.extend((r["symbol"], r["market_cap"] or 0) for r in rows)

            if us_syms:
                placeholders = ", ".join(f"${i+1}" for i in range(len(us_syms)))
                rows = await conn.fetch(
                    f"SELECT symbol, market_cap FROM us_stock_basic "
                    f"WHERE symbol IN ({placeholders}) "
                    f"ORDER BY market_cap DESC NULLS LAST",
                    *us_syms
                )
                ranked.extend((r["symbol"], r["market_cap"] or 0) for r in rows)

        # Sort by market cap descending, take top N
        ranked.sort(key=lambda x: x[1], reverse=True)
        selected = [r[0] for r in ranked[:limit]]

        # Preserve symbols not found in DB (edge case)
        if not selected:
            return symbols[:limit]

        return selected

    except Exception as e:
        logger.warning(f"[SupplementaryChart] Market cap selection failed: {e}")
        return symbols[:limit]


# ---------------------------------------------------------------------------
# Indicator data fetch (60-day fixed pattern)
# ---------------------------------------------------------------------------

async def _fetch_indicator_data(
    symbols: List[str],
    market_map: Dict[str, str],
    is_single: bool
) -> List[Dict]:
    """Fetch 60-day indicator history using fixed-pattern queries."""
    kr_syms = [s for s in symbols if market_map.get(s) == "KR"]
    us_syms = [s for s in symbols if market_map.get(s) == "US"]

    all_rows: List[Dict] = []

    async with db.pool.acquire() as conn:
        if kr_syms:
            rows = await _fetch_kr_indicators(conn, kr_syms, is_single)
            all_rows.extend(rows)

        if us_syms:
            rows = await _fetch_us_indicators(conn, us_syms, is_single)
            all_rows.extend(rows)

    return all_rows


async def _fetch_kr_indicators(conn, symbols: List[str], is_single: bool) -> List[Dict]:
    """Fetch KR indicator data with JOIN to kr_intraday_total for close price."""
    placeholders = ", ".join(f"${i+1}" for i in range(len(symbols)))

    if is_single:
        sql = f"""
            SELECT i.date, i.symbol, i.stock_name, k.close,
                   i.rsi, i.macd, i.macd_signal, i.macd_hist,
                   i.real_upper_band, i.real_middle_band, i.real_lower_band,
                   i.adx, i.mfi, i.slowk, i.slowd, i.sma, i.ema
            FROM kr_indicators i
            JOIN kr_intraday_total k ON i.symbol = k.symbol AND i.date = k.date
            WHERE i.symbol IN ({placeholders})
              AND i.date >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY i.date
        """
    else:
        sql = f"""
            SELECT i.date, i.symbol, i.stock_name, k.close,
                   i.rsi, i.adx, i.mfi, i.slowk, i.slowd
            FROM kr_indicators i
            JOIN kr_intraday_total k ON i.symbol = k.symbol AND i.date = k.date
            WHERE i.symbol IN ({placeholders})
              AND i.date >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY i.symbol, i.date
        """

    rows = await conn.fetch(sql, *symbols)
    return [dict(r) for r in rows]


async def _fetch_us_indicators(conn, symbols: List[str], is_single: bool) -> List[Dict]:
    """Fetch US indicator data with JOIN to us_daily for close price."""
    placeholders = ", ".join(f"${i+1}" for i in range(len(symbols)))

    if is_single:
        sql = f"""
            SELECT i.date, i.symbol, i.stock_name, d.close,
                   i.rsi, i.macd, i.macd_signal, i.macd_hist,
                   i.real_upper_band, i.real_middle_band, i.real_lower_band,
                   i.adx, i.mfi, i.slowk, i.slowd, i.sma, i.ema
            FROM us_indicators i
            JOIN us_daily d ON i.symbol = d.symbol AND i.date = d.date
            WHERE i.symbol IN ({placeholders})
              AND i.date >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY i.date
        """
    else:
        sql = f"""
            SELECT i.date, i.symbol, i.stock_name, d.close,
                   i.rsi, i.adx, i.mfi, i.slowk, i.slowd
            FROM us_indicators i
            JOIN us_daily d ON i.symbol = d.symbol AND i.date = d.date
            WHERE i.symbol IN ({placeholders})
              AND i.date >= CURRENT_DATE - INTERVAL '60 days'
            ORDER BY i.symbol, i.date
        """

    rows = await conn.fetch(sql, *symbols)
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Chart building
# ---------------------------------------------------------------------------

def _build_chart(
    rows: List[Dict],
    symbols: List[str],
    market_map: Dict[str, str],
    is_single: bool
) -> Dict[str, Any]:
    """Build multi_chart structure from indicator rows."""
    tabs = SINGLE_TABS if is_single else MULTI_TABS
    charts = []

    if is_single:
        charts = _build_single_stock_charts(rows, tabs)
    else:
        charts = _build_multi_stock_charts(rows, symbols, tabs)

    if not charts:
        return None

    # Determine title
    if is_single:
        stock_name = rows[0].get("stock_name", symbols[0]) if rows else symbols[0]
        title = f"{stock_name} - Technical Indicators (60D)"
    else:
        title = f"Technical Indicators ({len(symbols)} stocks, 60D)"

    return {
        "type": "multi_chart",
        "title": title,
        "data": {
            "charts": charts,
            "defaultIndex": 0,
        }
    }


def _build_single_stock_charts(rows: List[Dict], tabs: list) -> List[Dict]:
    """Build chart tabs for a single stock."""
    charts = []
    labels = _extract_date_labels(rows)

    for tab_label, col_keys in tabs:
        datasets = []
        for ci, col in enumerate(col_keys):
            data_points = []
            for row in rows:
                val = row.get(col)
                data_points.append(float(val) if val is not None else None)

            datasets.append({
                "label": COLUMN_LABELS.get(col, col),
                "data": data_points,
                "borderColor": CHART_COLORS[ci % len(CHART_COLORS)],
            })

        charts.append({
            "label": tab_label,
            "visualization": {
                "type": "line_chart",
                "data": {
                    "labels": labels,
                    "datasets": datasets,
                }
            }
        })

    return charts


def _build_multi_stock_charts(
    rows: List[Dict],
    symbols: List[str],
    tabs: list
) -> List[Dict]:
    """Build chart tabs for multiple stocks with overlay lines."""
    # Group rows by symbol
    by_symbol: Dict[str, List[Dict]] = {}
    for row in rows:
        sym = row.get("symbol", "")
        by_symbol.setdefault(sym, []).append(row)

    # Use the symbol with most data points for labels
    max_sym = max(by_symbol.keys(), key=lambda s: len(by_symbol[s])) if by_symbol else ""
    labels = _extract_date_labels(by_symbol.get(max_sym, []))

    # Build date -> index map for alignment
    date_index = {label: i for i, label in enumerate(labels)}

    charts = []
    for tab_label, col_keys in tabs:
        datasets = []
        for si, sym in enumerate(symbols):
            sym_rows = by_symbol.get(sym, [])
            if not sym_rows:
                continue

            stock_name = sym_rows[0].get("stock_name", sym)

            for col in col_keys:
                # Initialize with None for alignment
                data_points = [None] * len(labels)
                for row in sym_rows:
                    d = row.get("date")
                    if d:
                        date_str = str(d)[:10]
                        idx = date_index.get(date_str)
                        if idx is not None:
                            val = row.get(col)
                            data_points[idx] = float(val) if val is not None else None

                col_label = COLUMN_LABELS.get(col, col)
                ds_label = f"{stock_name}" if len(col_keys) == 1 else f"{stock_name} ({col_label})"
                datasets.append({
                    "label": ds_label,
                    "data": data_points,
                    "borderColor": CHART_COLORS[si % len(CHART_COLORS)],
                })

        charts.append({
            "label": tab_label,
            "visualization": {
                "type": "line_chart",
                "data": {
                    "labels": labels,
                    "datasets": datasets,
                }
            }
        })

    return charts


def _extract_date_labels(rows: List[Dict]) -> List[str]:
    """Extract date strings from rows for chart labels."""
    labels = []
    for row in rows:
        d = row.get("date")
        if d:
            labels.append(str(d)[:10])
        else:
            labels.append("")
    return labels
