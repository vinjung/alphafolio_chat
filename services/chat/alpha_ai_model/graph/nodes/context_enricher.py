# services/chat/alpha_ai_model/graph/nodes/context_enricher.py
"""
Context Enricher Node

Automatically retrieves supplementary data from DB to enrich LLM responses.
Runs multiple enrichment queries in parallel using asyncio.gather with
semaphore-based connection pool protection.

Categories:
- sector_comparison: Compare stock metrics with industry/sector averages
- indicator_trend: Recent trend of technical indicators
- investor_flow: Foreign/institutional investor flow (KR only)
- price_context: Price levels, MA positions, period high/low
- market_overview: Current market index status
"""
import asyncio
from typing import Dict, Any, List, Optional
from config import logger
from database import db


# Connection pool protection: max 3 concurrent enrichment queries
# Railway api POSTGRES_POOL_MAX=25, this prevents pool exhaustion
_enrichment_semaphore = asyncio.Semaphore(3)


# ============================================================================
# ENRICHMENT RULES - Rule-based category selection (no LLM call)
# ============================================================================

def _has_stock_codes(state: Dict[str, Any]) -> bool:
    """Check if stock codes are available from entities or SQL results"""
    entities = state.get("entities", {})
    return bool(entities.get("stock_codes") or entities.get("stock_codes_from_sql"))


ENRICHMENT_RULES = {
    "sector_comparison": {
        "condition": _has_stock_codes,
        "intents": ["query", "technical", "analysis", "ranking", "filter", "quant"],
    },
    "indicator_trend": {
        "condition": lambda s: (
            bool(s.get("entities", {}).get("indicators")) or _has_stock_codes(s)
        ),
        "intents": ["technical", "analysis", "query"],
    },
    "investor_flow": {
        # KR only - US has no investor flow table
        "condition": lambda s: (
            _has_stock_codes(s) and s.get("market") in ["KR", "BOTH"]
        ),
        "intents": ["query", "technical", "analysis", "investor"],
    },
    "price_context": {
        "condition": _has_stock_codes,
        "intents": ["query", "technical", "analysis"],
    },
    "market_overview": {
        "condition": lambda s: True,
        "intents": ["query", "technical", "analysis", "ranking", "filter", "market"],
    },
    "stock_grade": {
        "condition": _has_stock_codes,
        "intents": ["query", "technical", "analysis"],
    },
}


# ============================================================================
# CATEGORY SELECTION
# ============================================================================

def _select_enrichment_categories(state: Dict[str, Any]) -> List[str]:
    """Select which enrichment categories to run based on state"""
    intent = state.get("intent", "")
    selected = []

    for category, rule in ENRICHMENT_RULES.items():
        if intent not in rule["intents"]:
            continue
        if rule["condition"](state):
            selected.append(category)

    return selected


# ============================================================================
# SQL BUILDER - DB-verified templates (2026-02-10)
# ============================================================================

def _build_enrichment_sql(category: str, state: Dict[str, Any]) -> Optional[str]:
    """Build enrichment SQL query from template"""
    market = state.get("market", "KR")
    entities = state.get("entities", {})
    stock_codes = entities.get("stock_codes", [])
    # Fallback: use SQL-discovered stock codes if entity extractor found none
    if not stock_codes:
        stock_codes = entities.get("stock_codes_from_sql", [])
    symbol = stock_codes[0] if stock_codes else None

    if category == "sector_comparison":
        if not symbol:
            return None
        if market == "US":
            # us_stock_basic.sector exists (14 sectors)
            # us_daily.trading_value is all NULL, excluded
            return f"""
                SELECT COUNT(*) as sector_stock_count,
                    ROUND(AVG(i.rsi)::numeric, 1) as avg_rsi,
                    ROUND(AVG(i.macd)::numeric, 2) as avg_macd
                FROM us_indicators i
                JOIN us_stock_basic b ON i.symbol = b.symbol
                WHERE i.date = (SELECT MAX(date) FROM us_indicators)
                AND b.sector = (SELECT sector FROM us_stock_basic WHERE symbol = '{symbol}')
            """
        else:
            # KR: kr_stock_basic has no sector column
            # Use kr_stock_detail.industry instead
            return f"""
                SELECT COUNT(*) as sector_stock_count,
                    ROUND(AVG(i.rsi)::numeric, 1) as avg_rsi,
                    ROUND(AVG(i.macd)::numeric, 2) as avg_macd,
                    ROUND(AVG(t.change_rate)::numeric, 2) as avg_change_rate,
                    ROUND(AVG(t.trading_value)::numeric, 0) as avg_trading_value
                FROM kr_indicators i
                JOIN kr_intraday_total t ON i.symbol = t.symbol AND i.date = t.date
                JOIN kr_stock_detail d ON i.symbol = d.symbol
                WHERE i.date = (SELECT MAX(date) FROM kr_indicators)
                AND d.industry = (SELECT industry FROM kr_stock_detail WHERE symbol = '{symbol}')
            """

    elif category == "indicator_trend":
        if not symbol:
            return None
        table = "us_indicators" if market == "US" else "kr_indicators"
        return f"""
            SELECT date, rsi, macd, macd_signal, adx, mfi
            FROM {table}
            WHERE symbol = '{symbol}'
            AND date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY date ASC
        """

    elif category == "investor_flow":
        # KR only - US has no investor flow table
        if not symbol or market == "US":
            return None
        # Actual columns: foreign_net_volume/value, inst_net_volume/value, retail_net_volume/value
        # (NOT foreign_net, institution_net, retail_net)
        return f"""
            SELECT date,
                foreign_net_volume, foreign_net_value,
                inst_net_volume, inst_net_value,
                retail_net_volume, retail_net_value
            FROM kr_individual_investor_daily_trading
            WHERE symbol = '{symbol}'
            AND date >= CURRENT_DATE - INTERVAL '15 days'
            ORDER BY date ASC
        """

    elif category == "price_context":
        if not symbol:
            return None
        if market == "US":
            # us_daily.trading_value is all NULL, use volume only
            return f"""
                SELECT date, close, volume,
                    ROUND(AVG(close) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)::numeric, 2) as ma5,
                    ROUND(AVG(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)::numeric, 2) as ma20
                FROM us_daily
                WHERE symbol = '{symbol}'
                AND date >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY date ASC
            """
        else:
            return f"""
                SELECT date, close, volume,
                    ROUND(AVG(close) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW)::numeric, 0) as ma5,
                    ROUND(AVG(close) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)::numeric, 0) as ma20
                FROM kr_intraday_total
                WHERE symbol = '{symbol}'
                AND date >= CURRENT_DATE - INTERVAL '90 days'
                ORDER BY date ASC
            """

    elif category == "market_overview":
        # Column is 'exchange', NOT 'index_name'
        # Values: KOSPI, KOSDAQ, NASDAQ, DOW, S&P500
        if market == "US":
            exchanges = "('NASDAQ', 'DOW', 'S&P500')"
        elif market == "BOTH":
            exchanges = "('KOSPI', 'KOSDAQ', 'NASDAQ', 'DOW', 'S&P500')"
        else:
            exchanges = "('KOSPI', 'KOSDAQ')"
        return f"""
            SELECT exchange, close, change_rate, date
            FROM market_index
            WHERE date = (SELECT MAX(date) FROM market_index)
            AND exchange IN {exchanges}
        """

    elif category == "stock_grade":
        if not symbol:
            return None
        grade_table = "us_stock_grade" if market == "US" else "kr_stock_grade"
        return f"""
            SELECT g.symbol, g.stock_name, g.final_grade, g.final_score,
                   g.signal_overall, g.market_state,
                   g.scenario_bullish_prob, g.scenario_sideways_prob, g.scenario_bearish_prob,
                   g.scenario_bullish_return, g.scenario_sideways_return, g.scenario_bearish_return,
                   g.stop_loss_pct, g.take_profit_pct, g.risk_reward_ratio,
                   g.entry_timing_score, g.position_size_pct,
                   g.risk_profile_text, g.risk_recommendation
            FROM {grade_table} g
            WHERE g.symbol = '{symbol}'
              AND g.date = (SELECT MAX(date) FROM {grade_table} WHERE symbol = '{symbol}')
        """

    return None


# ============================================================================
# QUERY EXECUTION
# ============================================================================

async def _execute_enrichment_query(
    category: str, sql: str
) -> Optional[tuple]:
    """Execute a single enrichment query with semaphore protection and timeout"""
    async with _enrichment_semaphore:
        try:
            async with db.pool.acquire() as conn:
                rows = await asyncio.wait_for(
                    conn.fetch(sql),
                    timeout=5.0,
                )
                return (category, [dict(row) for row in rows])
        except asyncio.TimeoutError:
            logger.warning(f"[ContextEnricher] {category} query timed out (5s)")
            return None
        except Exception as e:
            logger.warning(f"[ContextEnricher] {category} query failed: {e}")
            return None


# ============================================================================
# RESULT FORMATTING
# ============================================================================

def _count_consecutive_sign(values: list) -> int:
    """Count consecutive days of same sign from the end of the list"""
    if not values:
        return 0
    last_sign = values[-1] >= 0
    count = 0
    for v in reversed(values):
        if (v >= 0) == last_sign:
            count += 1
        else:
            break
    return count


def _format_supplementary_context(
    enrichment_data: Dict[str, List[Dict]], state: Dict[str, Any]
) -> str:
    """Format enrichment results into structured text for LLM prompt"""
    sections = []
    market = state.get("market", "KR")

    # -- Sector/Industry comparison --
    if "sector_comparison" in enrichment_data:
        rows = enrichment_data["sector_comparison"]
        if rows:
            data = rows[0]  # Aggregation result is a single row
            label = "업종" if market != "US" else "섹터"
            lines = [
                f"[{label} 비교]",
                f"동일 {label} 종목 수: {data.get('sector_stock_count', 'N/A')}개",
                f"{label} 평균 RSI: {data.get('avg_rsi', 'N/A')}",
                f"{label} 평균 MACD: {data.get('avg_macd', 'N/A')}",
            ]
            if data.get("avg_change_rate") is not None:
                lines.append(f"{label} 평균 등락률: {data.get('avg_change_rate')}%")
            avg_tv = data.get("avg_trading_value")
            if avg_tv is not None and avg_tv > 0:
                lines.append(f"{label} 평균 거래대금: {avg_tv:,.0f}원")
            sections.append("\n".join(lines))

    # -- Indicator trend --
    if "indicator_trend" in enrichment_data:
        rows = enrichment_data["indicator_trend"]
        if len(rows) >= 2:
            first, last = rows[0], rows[-1]
            first_rsi = float(first.get("rsi") or 0)
            last_rsi = float(last.get("rsi") or 0)
            rsi_change = round(last_rsi - first_rsi, 1)
            sections.append(
                f"[지표 추이 ({len(rows)}일)]\n"
                f"RSI: {first.get('rsi')} -> {last.get('rsi')} (변화: {rsi_change:+.1f})\n"
                f"MACD: {first.get('macd')} -> {last.get('macd')}\n"
                f"ADX: {first.get('adx')} -> {last.get('adx')}"
            )

    # -- Investor flow (KR only) --
    if "investor_flow" in enrichment_data:
        rows = enrichment_data["investor_flow"]
        if rows:
            foreign_vols = [r.get("foreign_net_volume", 0) or 0 for r in rows]
            inst_vols = [r.get("inst_net_volume", 0) or 0 for r in rows]

            foreign_total_val = sum(r.get("foreign_net_value", 0) or 0 for r in rows)
            inst_total_val = sum(r.get("inst_net_value", 0) or 0 for r in rows)

            foreign_consec = _count_consecutive_sign(foreign_vols)
            inst_consec = _count_consecutive_sign(inst_vols)

            foreign_val_uk = abs(foreign_total_val) / 100_000_000
            inst_val_uk = abs(inst_total_val) / 100_000_000

            sections.append(
                f"[투자자 수급 ({len(rows)}일)]\n"
                f"외국인: {'순매수' if foreign_total_val > 0 else '순매도'} "
                f"{foreign_val_uk:,.0f}억원 ({foreign_consec}일 연속)\n"
                f"기관: {'순매수' if inst_total_val > 0 else '순매도'} "
                f"{inst_val_uk:,.0f}억원 ({inst_consec}일 연속)"
            )

    # -- Price context --
    if "price_context" in enrichment_data:
        rows = enrichment_data["price_context"]
        if rows:
            latest = rows[-1]
            closes = [float(r.get("close", 0)) for r in rows if r.get("close")]
            if closes:
                high_period = max(closes)
                low_period = min(closes)
                unit = "$" if market == "US" else "원"
                close_val = float(latest.get("close", 0))
                ma5_val = float(latest.get("ma5") or 0)
                ma20_val = float(latest.get("ma20") or 0)
                sections.append(
                    f"[가격 맥락]\n"
                    f"현재가: {close_val:,.0f}{unit}\n"
                    f"MA5: {ma5_val:,.0f}{unit} / MA20: {ma20_val:,.0f}{unit}\n"
                    f"기간 고가: {high_period:,.0f}{unit} / 기간 저가: {low_period:,.0f}{unit}"
                )

    # -- Market overview --
    if "market_overview" in enrichment_data:
        rows = enrichment_data["market_overview"]
        if rows:
            lines = ["[시장 현황]"]
            for r in rows:
                close_val = float(r.get("close", 0))
                change_val = float(r.get("change_rate", 0))
                lines.append(
                    f"{r.get('exchange')}: {close_val:,.2f} ({change_val:+.2f}%)"
                )
            sections.append("\n".join(lines))

    # -- Stock Grade (Investment Strategy) --
    if "stock_grade" in enrichment_data:
        rows = enrichment_data["stock_grade"]
        if rows:
            data = rows[0]
            lines = [
                f"[투자 등급]",
                f"종합등급: {data.get('final_grade', 'N/A')} (점수: {data.get('final_score', 'N/A')}/100)",
                f"종합신호: {data.get('signal_overall', 'N/A')}",
                f"시장상태: {data.get('market_state', 'N/A')}",
                f"",
                f"[시나리오 분석]",
                f"상승확률: {data.get('scenario_bullish_prob', 'N/A')}% (예상수익률: {data.get('scenario_bullish_return', 'N/A')})",
                f"횡보확률: {data.get('scenario_sideways_prob', 'N/A')}% (예상수익률: {data.get('scenario_sideways_return', 'N/A')})",
                f"하락확률: {data.get('scenario_bearish_prob', 'N/A')}% (예상수익률: {data.get('scenario_bearish_return', 'N/A')})",
                f"",
                f"[매매 기준]",
                f"손절가: {data.get('stop_loss_pct', 'N/A')}%",
                f"익절가: {data.get('take_profit_pct', 'N/A')}%",
                f"리스크/리워드: {data.get('risk_reward_ratio', 'N/A')}",
                f"진입타이밍점수: {data.get('entry_timing_score', 'N/A')}/100",
                f"권장비중: {data.get('position_size_pct', 'N/A')}%",
                f"리스크프로파일: {data.get('risk_profile_text', 'N/A')}",
                f"리스크권고: {data.get('risk_recommendation', 'N/A')}",
            ]
            sections.append("\n".join(lines))

    return "\n\n".join(sections) if sections else ""


# ============================================================================
# MAIN NODE
# ============================================================================

async def context_enricher(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Context auto-enrichment node with parallel SQL execution.

    Inserts between sql_executor and response_generator (or external_data_fetcher_hybrid).
    Retrieves supplementary data to enable deeper LLM analysis.

    Args:
        state: Current graph state with query_result from sql_executor

    Returns:
        Updated state with 'supplementary_context' field
    """
    logger.info("[AlphaAI:ContextEnricher] Processing...")

    intent = state.get("intent", "")
    query_result = state.get("query_result")

    # Skip conditions
    if not query_result or intent in ["chat", "explain"]:
        logger.info("[ContextEnricher] Skipped (no query_result or chat/explain intent)")
        return {
            **state,
            "supplementary_context": "",
            "processing_steps": state.get("processing_steps", []) + ["context_enricher"],
        }

    if not db.pool:
        logger.warning("[ContextEnricher] Database pool not available, skipping")
        return {
            **state,
            "supplementary_context": "",
            "processing_steps": state.get("processing_steps", []) + ["context_enricher"],
        }

    # 1. Select enrichment categories
    categories = _select_enrichment_categories(state)
    if not categories:
        logger.info("[ContextEnricher] No enrichment categories matched")
        return {
            **state,
            "supplementary_context": "",
            "processing_steps": state.get("processing_steps", []) + ["context_enricher"],
        }

    logger.info(f"[ContextEnricher] Selected categories: {categories}")

    # 2. Build SQL queries
    tasks = []
    for category in categories:
        sql = _build_enrichment_sql(category, state)
        if sql:
            tasks.append(_execute_enrichment_query(category, sql))

    # 3. Execute all in parallel (semaphore limits to 3 concurrent)
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        results = []

    # 4. Process results (skip failures)
    enrichment_data = {}
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"[ContextEnricher] Enrichment query exception: {result}")
            continue
        if result and isinstance(result, tuple):
            category_name, data = result
            if data:
                enrichment_data[category_name] = data

    # 5. Format into structured supplementary context
    supplementary_context = _format_supplementary_context(enrichment_data, state)

    logger.info(
        f"[ContextEnricher] Completed: {len(enrichment_data)}/{len(tasks)} categories enriched, "
        f"context length: {len(supplementary_context)} chars"
    )

    return {
        **state,
        "supplementary_context": supplementary_context,
        "processing_steps": state.get("processing_steps", []) + ["context_enricher"],
    }
