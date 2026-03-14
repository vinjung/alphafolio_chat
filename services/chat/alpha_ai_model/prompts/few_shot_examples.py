# services/chat/alpha_ai_model/prompts/few_shot_examples.py
"""
Few-Shot Examples for SQL Generation

Contains 148 example question-SQL pairs for few-shot prompting.
Organized by category for effective retrieval.
"""
from typing import List, Dict, Optional


# =============================================================================
# KOREAN STOCK EXAMPLES (kr_*)
# =============================================================================

KR_SIMPLE_QUERY_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "simple_query",
        "question": "네이버 시가총액",
        "sql": "SELECT symbol, stock_name, close, market_cap FROM kr_intraday WHERE symbol = '035420'",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "simple_query",
        "question": "현대차 오늘 주가",
        "sql": "SELECT symbol, stock_name, open, high, low, close, change_rate FROM kr_intraday WHERE symbol = '005380'",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_RANKING_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "ranking",
        "question": "거래대금 상위 10개 종목",
        "sql": "SELECT symbol, stock_name, close, trading_value, volume, change_rate FROM kr_intraday ORDER BY trading_value DESC LIMIT 10",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "ranking",
        "question": "상승률 상위 10개",
        "sql": "SELECT symbol, stock_name, close, change_rate, volume FROM kr_intraday WHERE change_rate > 0 ORDER BY change_rate DESC LIMIT 10",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "ranking",
        "question": "하락률 상위 10개",
        "sql": "SELECT symbol, stock_name, close, change_rate, volume FROM kr_intraday WHERE change_rate < 0 ORDER BY change_rate ASC LIMIT 10",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "ranking",
        "question": "5일 평균 거래대금 상위 50개",
        "sql": "SELECT symbol, stock_name, close, avg_trading_value_5d FROM kr_intraday ORDER BY avg_trading_value_5d DESC LIMIT 50",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_FILTER_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "filter",
        "question": "시총 1조 이상 종목",
        "sql": "SELECT symbol, stock_name, close, market_cap, trading_value FROM kr_intraday WHERE market_cap >= 1000000000000 ORDER BY market_cap DESC",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "filter",
        "question": "거래대금 1000억 이상",
        "sql": "SELECT symbol, stock_name, close, trading_value, volume FROM kr_intraday WHERE trading_value >= 100000000000 ORDER BY trading_value DESC",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "filter",
        "question": "오늘 5% 이상 상승한 종목",
        "sql": "SELECT symbol, stock_name, close, change_rate, volume, trading_value FROM kr_intraday WHERE change_rate >= 5 ORDER BY change_rate DESC",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_TECHNICAL_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "technical",
        "question": "RSI 30 이하 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, i.rsi, k.change_rate
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE i.rsi < 30 AND i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY i.rsi ASC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "technical",
        "question": "MACD 골든크로스 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, i.macd, i.macd_signal, i.macd_hist
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE i.macd > i.macd_signal AND i.macd_hist > 0 AND i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY i.macd_hist DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "technical",
        "question": "볼린저밴드 상단 돌파 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, i.real_upper_band, i.real_middle_band
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE k.close > i.real_upper_band AND i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY (k.close - i.real_upper_band) / i.real_upper_band DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "technical",
        "question": "이동평균선 위에 있는 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, i.sma
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE k.close > i.sma AND i.sma > 0 AND i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY (k.close - i.sma) / i.sma DESC
LIMIT 50""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "technical",
        "question": "이동평균 정배열 종목 (종가 > EMA > SMA)",
        "sql": """SELECT k.symbol, k.stock_name, k.close, i.ema, i.sma
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE k.close > i.ema AND i.ema > i.sma AND i.sma > 0 AND i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY k.market_cap DESC""",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_COMPLEX_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "complex",
        "question": "시총 1조 이상이면서 RSI 30 이하",
        "sql": """SELECT k.symbol, k.stock_name, k.close, k.market_cap, i.rsi
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE k.market_cap >= 1000000000000 AND i.rsi < 30 AND i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY k.market_cap DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "complex",
        "question": "시총 5조 이상 + 거래대금 500억 이상 + 상승",
        "sql": """SELECT k.symbol, k.stock_name, k.close, k.market_cap, k.trading_value, k.change_rate
FROM kr_intraday k
WHERE k.market_cap >= 5000000000000 AND k.trading_value >= 50000000000 AND k.change_rate > 0
ORDER BY k.change_rate DESC""",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_INVESTOR_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "investor",
        "question": "외국인 순매수 상위 10개",
        "sql": """SELECT k.symbol, k.stock_name, k.close, t.foreign_net_volume, t.foreign_net_value
FROM kr_intraday k
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol
WHERE t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading) AND t.foreign_net_volume > 0
ORDER BY t.foreign_net_volume DESC
LIMIT 10""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "investor",
        "question": "외국인+기관 동반 순매수",
        "sql": """SELECT k.symbol, k.stock_name, k.close, t.foreign_net_volume, t.inst_net_volume
FROM kr_intraday k
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol
WHERE t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading) AND t.foreign_net_volume > 0 AND t.inst_net_volume > 0
ORDER BY (t.foreign_net_volume + t.inst_net_volume) DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_QUANT_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "quant",
        "question": "퀀트 종합등급 매수 이상 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, g.final_grade, g.final_score
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.final_grade IN ('강력 매수', '매수', '매수 고려')
ORDER BY g.final_score DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "가치점수 70 이상 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, g.value_score, g.final_grade
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.value_score >= 70
ORDER BY g.value_score DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "퀄리티+가치 모두 고점수",
        "sql": """SELECT k.symbol, k.stock_name, k.close, g.quality_score, g.value_score, g.final_score
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.quality_score >= 70 AND g.value_score >= 70
ORDER BY g.final_score DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "고위험 종목 조회",
        "sql": """SELECT k.symbol, k.stock_name, k.close, g.final_grade, g.outlier_risk_score, g.risk_flag
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.risk_flag IN ('HIGH_RISK', 'EXTREME_RISK')
ORDER BY g.outlier_risk_score DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "저위험 매수등급 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, g.final_grade, g.final_score, g.risk_flag, g.conviction_score
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.final_grade IN ('강력 매수', '매수', '매수 고려') AND g.risk_flag = 'NORMAL'
ORDER BY g.final_score DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "대안 종목 추천이 있는 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, g.final_grade,
       g.alt_symbol, g.alt_stock_name, g.alt_final_grade, g.alt_final_score, g.alt_match_type
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.alt_symbol IS NOT NULL
ORDER BY g.final_score DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "성장주 뭐 있어?",
        "sql": """SELECT k.symbol, k.stock_name, k.close, k.change_rate,
       g.growth_score, g.momentum_score, g.final_grade, g.final_score
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.growth_score >= 70
ORDER BY g.growth_score DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "가치투자주 추천",
        "sql": """SELECT k.symbol, k.stock_name, k.close, k.per, k.pbr,
       g.value_score, g.quality_score, g.final_grade, g.final_score
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE g.value_score >= 70
ORDER BY g.value_score DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_MARKET_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "market",
        "question": "코스피 지수",
        "sql": "SELECT exchange, close, change_rate, volume, trading_value FROM market_index WHERE exchange = 'KOSPI' ORDER BY date DESC LIMIT 1",
        "market": "KR"
    },
    {
        "category": "market",
        "question": "최근 10일 코스피 추이",
        "sql": "SELECT date, close, change_rate, volume FROM market_index WHERE exchange = 'KOSPI' ORDER BY date DESC LIMIT 10",
        "market": "KR"
    },
    {
        "category": "market",
        "question": "지금 시장 어때?",
        "sql": """SELECT exchange, close, change_rate, date
FROM market_index
WHERE date = (SELECT MAX(date) FROM market_index)
  AND exchange IN ('KOSPI', 'KOSDAQ')
ORDER BY exchange""",
        "market": "KR"
    },
]

# =============================================================================
# CTE (WITH) EXAMPLES - Common Table Expressions
# =============================================================================

KR_CTE_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "cte",
        "question": "외국인 순매수 상위 30개 중 20일선 돌파 종목",
        "sql": """WITH top_foreign AS (
    SELECT k.symbol, k.stock_name, k.close, t.foreign_net_volume
    FROM kr_intraday k
    JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol
    WHERE t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading) AND t.foreign_net_volume > 0
    ORDER BY t.foreign_net_volume DESC
    LIMIT 30
)
SELECT tf.symbol, tf.stock_name, tf.close, tf.foreign_net_volume, i.sma
FROM top_foreign tf
JOIN kr_indicators i ON tf.symbol = i.symbol
WHERE tf.close > i.sma AND i.date = (SELECT MAX(date) FROM kr_indicators)""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "cte",
        "question": "기관 순매수 상위 20개와 퀀트 등급",
        "sql": """WITH top_institution AS (
    SELECT k.symbol, k.stock_name, k.close, t.inst_net_volume
    FROM kr_intraday k
    JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol
    WHERE t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading) AND t.inst_net_volume > 0
    ORDER BY t.inst_net_volume DESC
    LIMIT 20
)
SELECT ti.symbol, ti.stock_name, ti.close, ti.inst_net_volume, g.final_grade, g.final_score
FROM top_institution ti
JOIN kr_stock_grade g ON ti.symbol = g.symbol
WHERE g.final_grade IN ('강력 매수', '매수', '매수 고려')
ORDER BY ti.inst_net_volume DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "cte",
        "question": "상승률 상위 30개 중 거래대금 1000억 이상 종목",
        "sql": """WITH top_gainers AS (
    SELECT symbol, stock_name, close, change_rate, trading_value
    FROM kr_intraday
    WHERE change_rate > 0
    ORDER BY change_rate DESC
    LIMIT 30
)
SELECT symbol, stock_name, close, change_rate, trading_value
FROM top_gainers
WHERE trading_value >= 100000000000
ORDER BY change_rate DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "cte",
        "question": "최근 6개월 외국인 순매수 상위 30종목 중 20일 이동평균 돌파하고 거래량 급증한 종목",
        "sql": """WITH foreign_top AS (
    SELECT t.symbol, k.stock_name,
           SUM(t.foreign_net_volume) AS cumul_foreign_net
    FROM kr_individual_investor_daily_trading t
    JOIN kr_intraday k ON t.symbol = k.symbol
    WHERE t.date >= (SELECT MAX(date) FROM kr_individual_investor_daily_trading) - INTERVAL '6 months'
    GROUP BY t.symbol, k.stock_name
    HAVING SUM(t.foreign_net_volume) > 0
    ORDER BY cumul_foreign_net DESC
    LIMIT 30
),
sma_breakout AS (
    SELECT ft.symbol, ft.stock_name, ft.cumul_foreign_net,
           k.close, i.sma, k.volume, k.avg_volume_20d
    FROM foreign_top ft
    JOIN kr_intraday k ON ft.symbol = k.symbol
    JOIN kr_indicators i ON ft.symbol = i.symbol
        AND i.date = (SELECT MAX(date) FROM kr_indicators)
    WHERE k.close > i.sma
)
SELECT symbol, stock_name, cumul_foreign_net, close, sma, volume, avg_volume_20d
FROM sma_breakout
WHERE volume > avg_volume_20d * 1.5
ORDER BY cumul_foreign_net DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "cte",
        "question": "외국인+기관 동반 순매수 30일 누적 상위 종목 중 RSI 70 미만",
        "sql": """WITH investor_flow AS (
    SELECT t.symbol,
           SUM(t.foreign_net_volume) AS foreign_net_30d,
           SUM(t.inst_net_volume) AS inst_net_30d
    FROM kr_individual_investor_daily_trading t
    WHERE t.date >= (SELECT MAX(date) FROM kr_individual_investor_daily_trading) - INTERVAL '30 days'
    GROUP BY t.symbol
    HAVING SUM(t.foreign_net_volume) > 0 AND SUM(t.inst_net_volume) > 0
)
SELECT k.symbol, k.stock_name, k.close, k.change_rate, k.market_cap,
       inv.foreign_net_30d, inv.inst_net_30d,
       i.rsi, i.macd, i.macd_signal
FROM investor_flow inv
JOIN kr_intraday k ON inv.symbol = k.symbol
JOIN kr_indicators i ON inv.symbol = i.symbol
    AND i.date = (SELECT MAX(date) FROM kr_indicators)
WHERE i.rsi < 70
ORDER BY inv.foreign_net_30d DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "cte",
        "question": "거래량 급증 종목 중 매수 등급이면서 외국인 순매수인 종목",
        "sql": """WITH volume_surge AS (
    SELECT symbol, stock_name, close, change_rate, volume, avg_volume_20d, market_cap
    FROM kr_intraday
    WHERE volume > avg_volume_20d * 2 AND avg_volume_20d > 0
),
with_grade AS (
    SELECT vs.symbol, vs.stock_name, vs.close, vs.change_rate,
           vs.volume, vs.avg_volume_20d, vs.market_cap,
           g.final_grade, g.final_score, g.foreign_net_30d
    FROM volume_surge vs
    JOIN kr_stock_grade g ON vs.symbol = g.symbol
    WHERE g.final_grade IN ('강력 매수', '매수', '매수 고려')
      AND g.foreign_net_30d > 0
)
SELECT symbol, stock_name, close, change_rate, volume, avg_volume_20d,
       market_cap, final_grade, final_score, foreign_net_30d
FROM with_grade
ORDER BY final_score DESC""",
        "market": "KR",
        "chart_indicators": True
    },
]

# =============================================================================
# SCREENING EXAMPLES - Multi-condition CTE screening
# =============================================================================

KR_SCREENING_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "screening",
        "question": "[SCREENING QUERY - Use CTE to combine ALL conditions in ONE SQL] "
                    "PER이 업종평균 이하이고 RSI 30-50이며 MACD 양전환된 종목 필터링 "
                    "AND 최근 분기 영업이익이 전년동기 대비 증가한 종목 "
                    "AND 필터링된 종목의 목표가 대비 현재주가 괴리율 상위 5개",
        "sql": """WITH filtered AS (
    SELECT t.symbol, t.stock_name, t.close, t.per, i.rsi, i.macd, i.macd_signal
    FROM kr_intraday_total t
    JOIN kr_indicators i ON t.symbol = i.symbol
        AND i.date = (SELECT MAX(date) FROM kr_indicators)
    JOIN kr_stock_detail d ON t.symbol = d.symbol
    WHERE t.date = (SELECT MAX(date) FROM kr_intraday_total)
      AND t.per IS NOT NULL AND t.per > 0
      AND t.per < (SELECT AVG(t2.per) FROM kr_intraday_total t2
                   JOIN kr_stock_detail d2 ON t2.symbol = d2.symbol
                   WHERE d2.industry = d.industry AND t2.date = t.date
                     AND t2.per IS NOT NULL AND t2.per > 0)
      AND i.rsi BETWEEN 30 AND 50
      AND i.macd > i.macd_signal
),
with_profit_growth AS (
    SELECT DISTINCT fp.symbol FROM kr_financial_position fp
    WHERE fp.account_nm LIKE '%영업이익%' AND fp.sj_div = 'IS'
      AND fp.thstrm_amount IS NOT NULL AND fp.frmtrm_amount IS NOT NULL
      AND fp.thstrm_amount > fp.frmtrm_amount
),
combined AS (
    SELECT f.* FROM filtered f
    WHERE f.symbol IN (SELECT symbol FROM with_profit_growth)
),
ranked AS (
    SELECT c.symbol, c.stock_name, c.close, c.per, c.rsi, c.macd, c.macd_signal,
           r.target_price,
           ROUND((r.target_price - c.close) / NULLIF(c.close, 0) * 100, 2) AS target_gap_pct
    FROM combined c
    JOIN kr_research_reports r ON c.symbol = r.symbol
        AND r.date = (SELECT MAX(date) FROM kr_research_reports WHERE symbol = c.symbol)
    WHERE r.target_price IS NOT NULL AND r.target_price > c.close
)
SELECT symbol, stock_name, close, per, rsi, macd, macd_signal,
       target_price, target_gap_pct
FROM ranked ORDER BY target_gap_pct DESC LIMIT 5""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "screening",
        "question": "[SCREENING QUERY - Use CTE to combine ALL conditions in ONE SQL] "
                    "외국인+기관 동반 순매수이고 변동성 시장평균 이하인 종목 중 시가총액 상위 5개",
        "sql": """WITH investor_flow AS (
    SELECT t.symbol,
           SUM(t.foreign_net_volume) AS foreign_net_30d,
           SUM(t.inst_net_volume) AS inst_net_30d
    FROM kr_individual_investor_daily_trading t
    WHERE t.date >= (SELECT MAX(date) FROM kr_individual_investor_daily_trading) - INTERVAL '30 days'
    GROUP BY t.symbol
    HAVING SUM(t.foreign_net_volume) > 0 AND SUM(t.inst_net_volume) > 0
),
low_vol AS (
    SELECT g.symbol FROM kr_stock_grade g
    WHERE g.date = (SELECT MAX(date) FROM kr_stock_grade)
      AND g.volatility_annual < (SELECT AVG(volatility_annual) FROM kr_stock_grade
                                  WHERE date = (SELECT MAX(date) FROM kr_stock_grade)
                                    AND volatility_annual IS NOT NULL)
)
SELECT k.symbol, k.stock_name, k.close, k.market_cap,
       inv.foreign_net_30d, inv.inst_net_30d,
       g.volatility_annual, g.sharpe_ratio
FROM investor_flow inv
JOIN low_vol lv ON inv.symbol = lv.symbol
JOIN kr_intraday_total k ON inv.symbol = k.symbol
    AND k.date = (SELECT MAX(date) FROM kr_intraday_total)
JOIN kr_stock_grade g ON inv.symbol = g.symbol
    AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
ORDER BY k.market_cap DESC LIMIT 5""",
        "market": "KR",
        "chart_indicators": True
    },
]

# =============================================================================
# TIME SERIES EXAMPLES - Relative date queries
# =============================================================================

KR_TIME_SERIES_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "time_series",
        "question": "삼성전자 최근 5일 주가",
        "sql": """SELECT date, close, change_rate, volume
FROM kr_intraday_total
WHERE symbol = '005930'
ORDER BY date DESC
LIMIT 5""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "time_series",
        "question": "이번 주 거래대금 상위 10개",
        "sql": """SELECT symbol, stock_name, SUM(trading_value) as weekly_trading_value, AVG(close) as avg_close
FROM kr_intraday_total
WHERE date >= DATE_TRUNC('week', (SELECT MAX(date) FROM kr_intraday_total))
GROUP BY symbol, stock_name
ORDER BY weekly_trading_value DESC
LIMIT 10""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "time_series",
        "question": "이번 달 외국인 순매수 누적 상위 20개",
        "sql": """SELECT k.symbol, k.stock_name, SUM(t.foreign_net_volume) as monthly_foreign_net
FROM kr_intraday_total k
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol AND k.date = t.date
WHERE t.date >= DATE_TRUNC('month', (SELECT MAX(date) FROM kr_individual_investor_daily_trading))
GROUP BY k.symbol, k.stock_name
HAVING SUM(t.foreign_net_volume) > 0
ORDER BY monthly_foreign_net DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "time_series",
        "question": "최근 5일 연속 상승 종목",
        "sql": """SELECT symbol, stock_name, close, change_rate
FROM kr_intraday
WHERE symbol IN (
    SELECT symbol
    FROM kr_intraday_total
    WHERE date >= (SELECT MAX(date) FROM kr_intraday_total) - INTERVAL '5 days'
    GROUP BY symbol
    HAVING COUNT(*) = SUM(CASE WHEN change_rate > 0 THEN 1 ELSE 0 END)
)
ORDER BY change_rate DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "time_series",
        "question": "지난주 대비 거래량 급증 종목",
        "sql": """WITH this_week AS (
    SELECT symbol, AVG(volume) as this_week_vol
    FROM kr_intraday_total
    WHERE date >= DATE_TRUNC('week', (SELECT MAX(date) FROM kr_intraday_total))
    GROUP BY symbol
),
last_week AS (
    SELECT symbol, AVG(volume) as last_week_vol
    FROM kr_intraday_total
    WHERE date >= DATE_TRUNC('week', (SELECT MAX(date) FROM kr_intraday_total)) - INTERVAL '7 days'
      AND date < DATE_TRUNC('week', (SELECT MAX(date) FROM kr_intraday_total))
    GROUP BY symbol
)
SELECT k.symbol, k.stock_name, k.close,
       tw.this_week_vol, lw.last_week_vol,
       (tw.this_week_vol / NULLIF(lw.last_week_vol, 0) - 1) * 100 as volume_change_pct
FROM kr_intraday k
JOIN this_week tw ON k.symbol = tw.symbol
JOIN last_week lw ON k.symbol = lw.symbol
WHERE lw.last_week_vol > 0
ORDER BY volume_change_pct DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "time_series",
        "question": "최근 30일 수익률 상위 20개",
        "sql": """WITH price_30d AS (
    SELECT symbol,
           FIRST_VALUE(close) OVER (PARTITION BY symbol ORDER BY date ASC) as start_price,
           LAST_VALUE(close) OVER (PARTITION BY symbol ORDER BY date ASC
               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as end_price
    FROM kr_intraday_total
    WHERE date >= (SELECT MAX(date) FROM kr_intraday_total) - INTERVAL '30 days'
)
SELECT DISTINCT k.symbol, k.stock_name, k.close,
       ((p.end_price - p.start_price) / p.start_price * 100) as return_30d
FROM kr_intraday k
JOIN price_30d p ON k.symbol = p.symbol
WHERE p.start_price > 0
ORDER BY return_30d DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "time_series",
        "question": "최근 3일 기관 순매수 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close,
       SUM(t.inst_net_volume) as inst_net_3d,
       SUM(t.inst_net_value) as inst_value_3d
FROM kr_intraday k
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol
WHERE t.date >= (SELECT MAX(date) FROM kr_individual_investor_daily_trading) - INTERVAL '3 days'
GROUP BY k.symbol, k.stock_name, k.close
HAVING SUM(t.inst_net_volume) > 0
ORDER BY inst_net_3d DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
]

# =============================================================================
# WINDOW FUNCTION EXAMPLES
# =============================================================================

KR_WINDOW_FUNCTION_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "window_function",
        "question": "삼성전자 전일 대비 주가 변화",
        "sql": """SELECT
    date, close,
    LAG(close) OVER (ORDER BY date) as prev_close,
    close - LAG(close) OVER (ORDER BY date) as change_amount,
    ROUND((close - LAG(close) OVER (ORDER BY date)) / LAG(close) OVER (ORDER BY date) * 100, 2) as change_pct
FROM kr_intraday_total
WHERE symbol = '005930'
ORDER BY date DESC
LIMIT 10""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "window_function",
        "question": "종목별 시총 순위와 섹터 내 순위",
        "sql": """SELECT
    k.symbol, k.stock_name, k.market_cap, d.industry,
    ROW_NUMBER() OVER (ORDER BY k.market_cap DESC) as total_rank,
    DENSE_RANK() OVER (PARTITION BY d.industry ORDER BY k.market_cap DESC) as sector_rank
FROM kr_intraday k
JOIN kr_stock_detail d ON k.symbol = d.symbol
ORDER BY k.market_cap DESC
LIMIT 30""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "window_function",
        "question": "삼성전자 5일 이동평균 계산",
        "sql": """SELECT
    date, close,
    AVG(close) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as ma5_calc,
    SUM(volume) OVER (ORDER BY date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) as vol_5d_sum
FROM kr_intraday_total
WHERE symbol = '005930'
ORDER BY date DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "window_function",
        "question": "거래량 급등 종목 (전일 대비 2배 이상)",
        "sql": """WITH volume_compare AS (
    SELECT
        symbol, date, volume,
        LAG(volume) OVER (PARTITION BY symbol ORDER BY date) as prev_volume
    FROM kr_intraday_total
    WHERE date >= (SELECT MAX(date) FROM kr_intraday_total) - INTERVAL '2 days'
)
SELECT k.symbol, k.stock_name, k.close, k.volume,
       vc.prev_volume,
       ROUND(k.volume::numeric / NULLIF(vc.prev_volume, 0), 2) as volume_ratio
FROM kr_intraday k
JOIN volume_compare vc ON k.symbol = vc.symbol
WHERE vc.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND vc.prev_volume > 0
  AND k.volume >= vc.prev_volume * 2
ORDER BY volume_ratio DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
]

# =============================================================================
# CASE WHEN EXAMPLES
# =============================================================================

KR_CASE_WHEN_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "case_when",
        "question": "종목별 RSI 구간 분류",
        "sql": """SELECT
    k.symbol, k.stock_name, k.close, i.rsi,
    CASE
        WHEN i.rsi < 30 THEN 'oversold'
        WHEN i.rsi > 70 THEN 'overbought'
        ELSE 'neutral'
    END as rsi_status
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY i.rsi""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "case_when",
        "question": "시가총액 규모별 분류",
        "sql": """SELECT
    symbol, stock_name, close, market_cap,
    CASE
        WHEN market_cap >= 50000000000000 THEN 'mega_cap'
        WHEN market_cap >= 10000000000000 THEN 'large_cap'
        WHEN market_cap >= 1000000000000 THEN 'mid_cap'
        WHEN market_cap >= 100000000000 THEN 'small_cap'
        ELSE 'micro_cap'
    END as cap_category
FROM kr_intraday
ORDER BY market_cap DESC
LIMIT 50""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "case_when",
        "question": "등락률 구간별 종목 수",
        "sql": """SELECT
    CASE
        WHEN change_rate >= 10 THEN 'sharp_rise'
        WHEN change_rate >= 3 THEN 'rise'
        WHEN change_rate >= 0 THEN 'slight_rise'
        WHEN change_rate >= -3 THEN 'slight_fall'
        WHEN change_rate >= -10 THEN 'fall'
        ELSE 'sharp_fall'
    END as change_category,
    COUNT(*) as stock_count,
    AVG(trading_value) as avg_trading_value
FROM kr_intraday
GROUP BY
    CASE
        WHEN change_rate >= 10 THEN 'sharp_rise'
        WHEN change_rate >= 3 THEN 'rise'
        WHEN change_rate >= 0 THEN 'slight_rise'
        WHEN change_rate >= -3 THEN 'slight_fall'
        WHEN change_rate >= -10 THEN 'fall'
        ELSE 'sharp_fall'
    END
ORDER BY
    CASE change_category
        WHEN 'sharp_rise' THEN 1
        WHEN 'rise' THEN 2
        WHEN 'slight_rise' THEN 3
        WHEN 'slight_fall' THEN 4
        WHEN 'fall' THEN 5
        ELSE 6
    END""",
        "market": "KR"
    },
]

# =============================================================================
# ADVANCED JOIN EXAMPLES (3+ tables)
# =============================================================================

KR_ADVANCED_JOIN_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "advanced_join",
        "question": "시총 상위 종목의 기술적 지표와 투자자 동향",
        "sql": """SELECT
    k.symbol, k.stock_name, k.close, k.market_cap,
    i.rsi, i.macd, i.sma,
    t.foreign_net_volume, t.inst_net_volume
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol AND i.date = (SELECT MAX(date) FROM kr_indicators)
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol AND t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading)
ORDER BY k.market_cap DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "advanced_join",
        "question": "퀀트 매수등급 종목의 기술적 분석과 수급",
        "sql": """SELECT
    k.symbol, k.stock_name, k.close,
    g.final_grade, g.final_score,
    i.rsi, i.macd, i.macd_signal,
    t.foreign_net_volume, t.inst_net_volume
FROM kr_intraday k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
JOIN kr_indicators i ON k.symbol = i.symbol AND i.date = (SELECT MAX(date) FROM kr_indicators)
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol AND t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading)
WHERE g.final_grade IN ('강력 매수', '매수', '매수 고려')
ORDER BY g.final_score DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "advanced_join",
        "question": "거래대금 상위 + RSI + MACD + 수급 종합",
        "sql": """SELECT
    k.symbol, k.stock_name, k.close, k.trading_value,
    i.rsi,
    CASE WHEN i.macd > i.macd_signal THEN 'bullish' ELSE 'bearish' END as macd_status,
    t.foreign_net_volume, t.inst_net_volume,
    (t.foreign_net_volume + t.inst_net_volume) as total_inst_foreign
FROM kr_intraday k
JOIN kr_indicators i ON k.symbol = i.symbol AND i.date = (SELECT MAX(date) FROM kr_indicators)
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol AND t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading)
ORDER BY k.trading_value DESC
LIMIT 30""",
        "market": "KR",
        "chart_indicators": True
    },
]


# =============================================================================
# US STOCK EXAMPLES (us_*)
# =============================================================================

US_SIMPLE_QUERY_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "simple_query",
        "question": "애플 주가",
        "sql": "SELECT d.symbol, s.stock_name, d.close, d.change_rate, d.volume FROM us_daily d JOIN us_stock_basic s ON d.symbol = s.symbol WHERE d.symbol = 'AAPL' ORDER BY date DESC LIMIT 1",
        "market": "US",
        "chart_indicators": True
    },
]

US_RANKING_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "ranking",
        "question": "미국 거래량 상위 10개",
        "sql": "SELECT d.symbol, s.stock_name, d.close, d.volume, d.change_rate FROM us_daily d JOIN us_stock_basic s ON d.symbol = s.symbol WHERE d.date = (SELECT MAX(date) FROM us_daily) ORDER BY d.volume DESC LIMIT 10",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "ranking",
        "question": "나스닥 상승률 상위 10개",
        "sql": "SELECT d.symbol, s.stock_name, d.close, d.change_rate, d.volume FROM us_daily d JOIN us_stock_basic s ON d.symbol = s.symbol WHERE d.date = (SELECT MAX(date) FROM us_daily) AND d.change_rate > 0 ORDER BY d.change_rate DESC LIMIT 10",
        "market": "US",
        "chart_indicators": True
    },
]

US_TECHNICAL_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "technical",
        "question": "미국 RSI 30 이하 종목",
        "sql": """SELECT d.symbol, d.close, i.rsi
FROM us_daily d
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.rsi < 30 AND d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY i.rsi ASC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
]

US_MARKET_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "market",
        "question": "나스닥 지수",
        "sql": "SELECT exchange, close, change_rate, volume FROM market_index WHERE exchange = 'NASDAQ' ORDER BY date DESC LIMIT 1",
        "market": "US"
    },
    {
        "category": "market",
        "question": "S&P 500 지수",
        "sql": "SELECT exchange, close, change_rate, volume FROM market_index WHERE exchange = 'NYSE' ORDER BY date DESC LIMIT 1",
        "market": "US"
    },
    {
        "category": "market",
        "question": "VIX 지수",
        "sql": "SELECT date, value FROM us_vix ORDER BY date DESC LIMIT 1",
        "market": "US"
    },
    {
        "category": "market",
        "question": "미국 시장 어때?",
        "sql": """WITH market AS (
    SELECT exchange, close, change_rate, date
    FROM market_index
    WHERE date = (SELECT MAX(date) FROM market_index)
      AND exchange IN ('NASDAQ', 'S&P500')
),
vix AS (
    SELECT value as vix_value, date as vix_date
    FROM us_vix ORDER BY date DESC LIMIT 1
),
regime AS (
    SELECT regime, vix_proxy, spy_return_1m, spy_ma200_distance
    FROM us_market_regime ORDER BY created_at DESC LIMIT 1
)
SELECT m.exchange, m.close, m.change_rate, m.date,
       v.vix_value, r.regime, r.spy_return_1m, r.spy_ma200_distance
FROM market m
CROSS JOIN vix v
CROSS JOIN regime r""",
        "market": "US"
    },
]

US_MACRO_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "macro",
        "question": "미국 기준금리",
        "sql": "SELECT date, value FROM us_fed_funds_rate ORDER BY date DESC LIMIT 1",
        "market": "US"
    },
    {
        "category": "macro",
        "question": "미국 10년물 국채 금리",
        "sql": "SELECT date, value FROM us_treasury_yield ORDER BY date DESC LIMIT 1",
        "market": "US"
    },
    {
        "category": "macro",
        "question": "미국 CPI",
        "sql": "SELECT date, value FROM us_cpi ORDER BY date DESC LIMIT 1",
        "market": "US"
    },
    {
        "category": "macro",
        "question": "미국 실업률",
        "sql": "SELECT date, value FROM us_unemployment_rate ORDER BY date DESC LIMIT 1",
        "market": "US"
    },
]


# =============================================================================
# DIVERGENT/OPPOSITE QUERY EXAMPLES (NEW)
# =============================================================================

KR_DIVERGENT_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "divergent",
        "question": "등락률이 극단적으로 갈린 2개 종목",
        "sql": """(SELECT symbol, stock_name, close, change_rate
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY change_rate DESC
LIMIT 1)
UNION ALL
(SELECT symbol, stock_name, close, change_rate
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY change_rate ASC
LIMIT 1)""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "divergent",
        "question": "외국인 순매수가 가장 많은 종목과 순매도가 가장 많은 종목",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, t.foreign_net_volume
FROM kr_intraday k
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol
WHERE t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading)
ORDER BY t.foreign_net_volume DESC
LIMIT 1)
UNION ALL
(SELECT k.symbol, k.stock_name, k.close, t.foreign_net_volume
FROM kr_intraday k
JOIN kr_individual_investor_daily_trading t ON k.symbol = t.symbol
WHERE t.date = (SELECT MAX(date) FROM kr_individual_investor_daily_trading)
ORDER BY t.foreign_net_volume ASC
LIMIT 1)""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "divergent",
        "question": "동일 업종 내 주가 흐름이 가장 다른 2개 종목 비교",
        "sql": """WITH sector_stocks AS (
    SELECT k.symbol, k.stock_name, k.close, k.change_rate
    FROM kr_intraday_total k
    JOIN kr_stock_detail d ON k.symbol = d.symbol
    WHERE d.industry LIKE '%반도체%'
    AND k.date = (SELECT MAX(date) FROM kr_intraday_total)
)
(SELECT symbol, stock_name, close, change_rate FROM sector_stocks ORDER BY change_rate DESC LIMIT 1)
UNION ALL
(SELECT symbol, stock_name, close, change_rate FROM sector_stocks ORDER BY change_rate ASC LIMIT 1)""",
        "market": "KR",
        "chart_indicators": True
    },
]

# =============================================================================
# KR FINANCIAL / CORPORATE EXAMPLES (NEW)
# =============================================================================

KR_FINANCIAL_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "financial",
        "question": "배당수익률 5% 이상 종목",
        "sql": """SELECT symbol, stock_name, close, dividend_yield, dps
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total) AND dividend_yield >= 5
ORDER BY dividend_yield DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "financial",
        "question": "부채비율 관련 재무 데이터 대형주",
        "sql": """SELECT k.symbol, k.stock_name, k.close, k.market_cap,
  f.account_nm, f.thstrm_amount
FROM kr_intraday k
JOIN kr_financial_position f ON k.symbol = f.symbol
WHERE f.account_nm LIKE '%부채총계%' AND f.fs_div = 'CFS'
  AND f.bsns_year = (SELECT MAX(bsns_year) FROM kr_financial_position)
  AND k.market_cap >= 10000000000000
ORDER BY k.market_cap DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "financial",
        "question": "ROE 15% 이상 고수익 기업",
        "sql": """SELECT k.symbol, k.stock_name, k.close, t.roe, t.per, t.pbr
FROM kr_intraday k
JOIN kr_intraday_total t ON k.symbol = t.symbol
WHERE t.date = (SELECT MAX(date) FROM kr_intraday_total) AND t.roe >= 15
ORDER BY t.roe DESC
LIMIT 30""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "financial",
        "question": "최대주주 지분율 50% 이상 종목",
        "sql": """SELECT DISTINCT ON (k.symbol) k.symbol, k.stock_name, k.close, l.nm, l.trmend_posesn_stock_qota_rt
FROM kr_intraday k
JOIN kr_largest_shareholder l ON k.symbol = l.symbol
WHERE l.trmend_posesn_stock_qota_rt >= 50
ORDER BY k.symbol, l.trmend_posesn_stock_qota_rt DESC""",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_SECTOR_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "sector",
        "question": "오늘 섹터별 수익률",
        "sql": """SELECT sector_code, avg_return_30d, stock_count, sector_rank
FROM mv_sector_daily_performance
WHERE date = (SELECT MAX(date) FROM mv_sector_daily_performance)
ORDER BY sector_rank ASC""",
        "market": "KR"
    },
    {
        "category": "sector",
        "question": "반도체 업종 종목 목록",
        "sql": """SELECT k.symbol, k.stock_name, k.close, k.change_rate, d.industry
FROM kr_intraday k
JOIN kr_stock_detail d ON k.symbol = d.symbol
WHERE d.industry LIKE '%반도체%'
ORDER BY k.market_cap DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "sector",
        "question": "IT 섹터 벤치마크 대비 수익률",
        "sql": """SELECT b.index_name, b.close, b.change_rate, b.volume
FROM kr_benchmark_index b
WHERE b.index_name LIKE '%IT%' OR b.index_name LIKE '%기술%'
ORDER BY b.date DESC
LIMIT 5""",
        "market": "KR"
    },
]

KR_CORPORATE_ACTION_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "corporate_action",
        "question": "오늘 대량매매 발생 종목",
        "sql": """SELECT b.symbol, b.stock_name, b.close, b.block_volume, b.block_volume_rate
FROM kr_blocktrades b
WHERE b.date = (SELECT MAX(date) FROM kr_blocktrades)
ORDER BY b.block_volume DESC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "corporate_action",
        "question": "최근 임원 변동 종목",
        "sql": """SELECT e.symbol, e.corp_name, e.nm, e.ofcps, e.chrg_job, e.stlm_dt
FROM kr_executive e
WHERE e.stlm_dt >= (SELECT MAX(stlm_dt) FROM kr_executive) - INTERVAL '90 days'
ORDER BY e.stlm_dt DESC
LIMIT 20""",
        "market": "KR"
    },
    {
        "category": "corporate_action",
        "question": "내부자 주식 취득 공시 종목",
        "sql": """SELECT s.symbol, s.corp_name, s.acqs_mth1, s.change_qy_acqs, s.trmend_qy, s.stlm_dt
FROM kr_stockacquisitiondisposal s
WHERE s.change_qy_acqs > 0 AND s.stlm_dt >= (SELECT MAX(stlm_dt) FROM kr_stockacquisitiondisposal) - INTERVAL '90 days'
ORDER BY s.stlm_dt DESC
LIMIT 20""",
        "market": "KR"
    },
]

KR_OWNERSHIP_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "ownership",
        "question": "외국인 지분율 높은 종목",
        "sql": """SELECT f.symbol, f.stock_name, f.close, f.foreign_rate, f.foreign_ownership
FROM kr_foreign_ownership f
WHERE f.date = (SELECT MAX(date) FROM kr_foreign_ownership) AND f.foreign_rate > 0
ORDER BY f.foreign_rate DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
]

KR_RESEARCH_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "research",
        "question": "삼성전자 최근 애널리스트 리포트",
        "sql": """SELECT symbol, stock_name, title, securities_firm, target_price, investment_opinion, date
FROM kr_research_reports
WHERE symbol = '005930'
ORDER BY date DESC
LIMIT 10""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "research",
        "question": "목표가 상향 종목",
        "sql": """SELECT k.symbol, k.stock_name, k.close, r.target_price, r.investment_opinion, r.securities_firm
FROM kr_intraday k
JOIN kr_research_reports r ON k.symbol = r.symbol
WHERE r.date >= (SELECT MAX(date) FROM kr_research_reports) - INTERVAL '7 days'
  AND r.target_price > k.close * 1.2
ORDER BY (r.target_price / k.close) DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
]

# =============================================================================
# KR ANALYSIS EXAMPLES (comprehensive single-stock analysis, 90-day time series)
# =============================================================================

KR_ANALYSIS_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "analysis",
        "question": "삼성전자 분석해줘",
        "sql": """SELECT t.date, t.open, t.high, t.low, t.close, t.volume, t.change_rate,
    t.market_cap, t.trading_value, t.per, t.pbr,
    i.rsi, i.macd, i.macd_signal, i.macd_hist,
    i.real_upper_band, i.real_middle_band, i.real_lower_band,
    i.sma, i.atr, i.slowk, i.slowd, i.adx
FROM kr_intraday_total t
LEFT JOIN kr_indicators i ON t.symbol = i.symbol AND t.date = i.date
WHERE t.symbol = '005930'
  AND t.date >= (SELECT MAX(date) FROM kr_intraday_total WHERE symbol = '005930') - INTERVAL '90 days'
ORDER BY t.date ASC""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "analysis",
        "question": "삼성전자와 SK하이닉스 비교 분석해줘",
        "sql": """SELECT t.symbol, t.stock_name, t.date, t.open, t.high, t.low, t.close, t.volume, t.change_rate,
    i.rsi, i.macd, i.macd_signal, i.macd_hist,
    i.real_upper_band, i.real_middle_band, i.real_lower_band,
    i.sma, i.atr, i.slowk, i.slowd, i.adx
FROM kr_intraday_total t
LEFT JOIN kr_indicators i ON t.symbol = i.symbol AND t.date = i.date
WHERE t.symbol IN ('005930', '000660')
  AND t.date >= (SELECT MAX(date) FROM kr_intraday_total WHERE symbol = '005930') - INTERVAL '90 days'
ORDER BY t.symbol, t.date ASC""",
        "market": "KR",
        "chart_indicators": True
    },
]

# =============================================================================
# US ANALYSIS EXAMPLES (comprehensive single-stock analysis, 90-day time series)
# =============================================================================

US_ANALYSIS_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "analysis",
        "question": "테슬라 분석해줘",
        "sql": """SELECT t.date, t.open, t.high, t.low, t.close, t.volume, t.change_rate,
    t.trading_value, t.per, t.pbr,
    i.rsi, i.macd, i.macd_signal, i.macd_hist,
    i.real_upper_band, i.real_middle_band, i.real_lower_band,
    i.sma, i.atr, i.slowk, i.slowd, i.adx
FROM us_daily t
LEFT JOIN us_indicators i ON t.symbol = i.symbol AND t.date = i.date
WHERE t.symbol = 'TSLA'
  AND t.date >= (SELECT MAX(date) FROM us_daily WHERE symbol = 'TSLA') - INTERVAL '90 days'
ORDER BY t.date ASC""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "analysis",
        "question": "애플과 마이크로소프트 비교 분석해줘",
        "sql": """SELECT t.symbol, t.date, t.open, t.high, t.low, t.close, t.volume, t.change_rate,
    i.rsi, i.macd, i.macd_signal, i.macd_hist,
    i.real_upper_band, i.real_middle_band, i.real_lower_band,
    i.sma, i.atr, i.slowk, i.slowd, i.adx
FROM us_daily t
LEFT JOIN us_indicators i ON t.symbol = i.symbol AND t.date = i.date
WHERE t.symbol IN ('AAPL', 'MSFT')
  AND t.date >= (SELECT MAX(date) FROM us_daily WHERE symbol = 'AAPL') - INTERVAL '90 days'
ORDER BY t.symbol, t.date ASC""",
        "market": "US",
        "chart_indicators": True
    },
]

# =============================================================================
# US FINANCIAL / CORPORATE EXAMPLES (NEW)
# =============================================================================

US_FINANCIAL_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "financial",
        "question": "애플 최근 매출과 순이익",
        "sql": """SELECT fiscal_date_ending, total_revenue, net_income, gross_profit, operating_income
FROM us_income_statement
WHERE symbol = 'AAPL'
ORDER BY fiscal_date_ending DESC
LIMIT 4""",
        "market": "US"
    },
    {
        "category": "financial",
        "question": "테슬라 총자산과 부채",
        "sql": """SELECT fiscal_date_ending, total_assets, total_liabilities, total_shareholder_equity, long_term_debt
FROM us_balance_sheet
WHERE symbol = 'TSLA'
ORDER BY fiscal_date_ending DESC
LIMIT 4""",
        "market": "US"
    },
    {
        "category": "financial",
        "question": "엔비디아 영업현금흐름",
        "sql": """SELECT fiscal_date_ending, operating_cashflow, capital_expenditures,
  (operating_cashflow + capital_expenditures) as free_cash_flow
FROM us_cash_flow
WHERE symbol = 'NVDA'
ORDER BY fiscal_date_ending DESC
LIMIT 4""",
        "market": "US"
    },
    {
        "category": "financial",
        "question": "미국 배당수익률 상위 10개",
        "sql": """SELECT s.symbol, s.stock_name, s.dividendyield, s.dividendpershare, s.exdividenddate
FROM us_stock_basic s
WHERE s.dividendyield > 0
ORDER BY s.dividendyield DESC
LIMIT 10""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "financial",
        "question": "미국 배당금 가장 많이 주는 주식 10개",
        "sql": """SELECT d.symbol, s.stock_name, d.amount, d.ex_dividend_date
FROM us_dividends d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.ex_dividend_date >= (SELECT MAX(ex_dividend_date) FROM us_dividends) - INTERVAL '3 months'
  AND d.ex_dividend_date <= (SELECT MAX(ex_dividend_date) FROM us_dividends)
ORDER BY d.amount DESC
LIMIT 10""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "financial",
        "question": "배당 예정일이 이번 달인 미국 주식",
        "sql": """SELECT d.symbol, s.stock_name, d.ex_dividend_date, d.amount, d.payment_date
FROM us_dividends d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.ex_dividend_date >= DATE_TRUNC('month', (SELECT MAX(ex_dividend_date) FROM us_dividends))
  AND d.ex_dividend_date < DATE_TRUNC('month', (SELECT MAX(ex_dividend_date) FROM us_dividends)) + INTERVAL '1 month'
ORDER BY d.ex_dividend_date""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "financial",
        "question": "한국 배당금 높은 주식 순위",
        "sql": """SELECT symbol, stock_name, close, dps, dividend_yield
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total) AND dps > 0
ORDER BY dps DESC
LIMIT 10""",
        "market": "KR",
        "chart_indicators": True
    },
]

US_EARNINGS_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "earnings",
        "question": "이번 주 실적 발표 예정 기업",
        "sql": """SELECT symbol, name, reportdate, estimate, fiscaldateending
FROM us_earnings_calendar
WHERE reportdate BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
ORDER BY reportdate""",
        "market": "US"
    },
    {
        "category": "earnings",
        "question": "애플 EPS 컨센서스",
        "sql": """SELECT symbol, estimate_date, horizon, eps_estimate_average, eps_estimate_high, eps_estimate_low, eps_estimate_analyst_count
FROM us_earnings_estimates
WHERE symbol = 'AAPL'
ORDER BY estimate_date DESC
LIMIT 8""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "earnings",
        "question": "EPS 컨센서스 상향 조정 종목",
        "sql": """SELECT e.symbol, s.stock_name, e.horizon,
  e.eps_estimate_average, e.eps_estimate_average_30_days_ago,
  ROUND((e.eps_estimate_average - e.eps_estimate_average_30_days_ago)
    / NULLIF(ABS(e.eps_estimate_average_30_days_ago), 0) * 100, 2) as revision_pct,
  e.eps_estimate_analyst_count
FROM us_earnings_estimates e
JOIN us_stock_basic s ON e.symbol = s.symbol
WHERE e.estimate_date = (SELECT MAX(estimate_date) FROM us_earnings_estimates)
  AND e.horizon = 'current_quarter'
  AND e.eps_estimate_average > e.eps_estimate_average_30_days_ago
ORDER BY revision_pct DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
]

US_OPTIONS_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "options",
        "question": "풋콜비율 1.5 이상 종목",
        "sql": """SELECT o.symbol, s.stock_name,
  ROUND(o.total_put_volume::numeric / NULLIF(o.total_call_volume, 0), 2) as put_call_ratio,
  o.total_call_volume, o.total_put_volume
FROM us_option_daily_summary o
JOIN us_stock_basic s ON o.symbol = s.symbol
WHERE o.date = (SELECT MAX(date) FROM us_option_daily_summary)
  AND o.total_call_volume > 0
  AND o.total_put_volume::numeric / NULLIF(o.total_call_volume, 0) >= 1.5
ORDER BY put_call_ratio DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "options",
        "question": "옵션 거래량 급증 종목",
        "sql": """SELECT o.symbol, s.stock_name,
  (o.total_call_volume + o.total_put_volume) as total_volume,
  o.avg_implied_volatility,
  ROUND(o.total_put_volume::numeric / NULLIF(o.total_call_volume, 0), 2) as put_call_ratio
FROM us_option_daily_summary o
JOIN us_stock_basic s ON o.symbol = s.symbol
WHERE o.date = (SELECT MAX(date) FROM us_option_daily_summary)
ORDER BY total_volume DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
]

US_CORPORATE_ACTION_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "corporate_action",
        "question": "최근 주식분할 종목",
        "sql": """SELECT symbol, effective_date, split_factor
FROM us_splits
WHERE effective_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY effective_date DESC""",
        "market": "US"
    },
    {
        "category": "corporate_action",
        "question": "이번 달 IPO 예정 기업",
        "sql": """SELECT name, symbol, ipodate, pricerangelow, pricerangehigh, exchange
FROM us_ipo_calendar
WHERE ipodate BETWEEN DATE_TRUNC('month', CURRENT_DATE) AND DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month'
ORDER BY ipodate""",
        "market": "US"
    },
    {
        "category": "corporate_action",
        "question": "내부자 매수 종목",
        "sql": """SELECT i.symbol, s.stock_name, i.executive, i.acquisition_or_disposal, i.shares, i.share_price, i.date
FROM us_insider_transactions i
JOIN us_stock_basic s ON i.symbol = s.symbol
WHERE i.acquisition_or_disposal = 'A' AND i.date >= (SELECT MAX(date) FROM us_insider_transactions) - INTERVAL '30 days'
ORDER BY i.shares * i.share_price DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
]

US_NEWS_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "news",
        "question": "Show recent Tesla news and sentiment",
        "sql": """SELECT title, time_published, overall_sentiment_score, overall_sentiment_label,
    ticker_sentiment_score, ticker_sentiment_label, source, url
FROM us_news
WHERE ticker = 'TSLA'
ORDER BY time_published DESC
LIMIT 20""",
        "market": "US"
    },
]

US_QUANT_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "quant",
        "question": "미국 퀀트 등급 매수 이상 종목",
        "sql": """SELECT d.symbol, s.stock_name, d.close, g.final_grade, g.final_score
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE g.final_grade IN ('강력 매수', '매수', '매수 고려') AND d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY g.final_score DESC
LIMIT 30""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "미국 저위험 매수 종목",
        "sql": """SELECT d.symbol, s.stock_name, d.close, g.final_grade, g.final_score, g.risk_flag, g.conviction_score
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE g.final_grade IN ('강력 매수', '매수', '매수 고려') AND g.risk_flag = 'NORMAL' AND d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY g.final_score DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "미국 대안 종목 추천 조회",
        "sql": """SELECT d.symbol, s.stock_name, d.close, g.final_grade,
       g.alt_symbol, g.alt_stock_name, g.alt_final_grade, g.alt_match_type
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE g.alt_symbol IS NOT NULL AND d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY g.final_score DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "미국 성장주 뭐 있어?",
        "sql": """SELECT d.symbol, s.stock_name, d.close, d.change_rate,
       g.growth_score, g.momentum_score, g.final_grade, g.final_score
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE g.growth_score >= 70 AND d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY g.growth_score DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "미국 가치투자주 추천",
        "sql": """SELECT d.symbol, s.stock_name, d.close,
       g.value_score, g.quality_score, g.final_grade, g.final_score
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE g.value_score >= 70 AND d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY g.value_score DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
]

US_SECTOR_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "sector",
        "question": "미국 섹터별 수익률",
        "sql": """SELECT sector_code, avg_return_30d, stock_count, sector_rank
FROM mv_us_sector_daily_performance
WHERE date = (SELECT MAX(date) FROM mv_us_sector_daily_performance)
ORDER BY sector_rank ASC""",
        "market": "US"
    },
    {
        "category": "sector",
        "question": "IT 섹터 벤치마크",
        "sql": """SELECT sector, pe_median, gross_margin_median, roe_median, revenue_growth_median
FROM us_sector_benchmarks
WHERE sector = 'TECHNOLOGY'
ORDER BY date DESC
LIMIT 1""",
        "market": "US"
    },
]

US_VOLATILITY_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "volatility",
        "question": "VIX 추이",
        "sql": """SELECT date, value
FROM us_vix
ORDER BY date DESC
LIMIT 20""",
        "market": "US"
    },
    {
        "category": "volatility",
        "question": "채권 변동성 MOVE 지수",
        "sql": """SELECT date, value
FROM us_move_index
ORDER BY date DESC
LIMIT 10""",
        "market": "US"
    },
    {
        "category": "volatility",
        "question": "달러 인덱스 추이",
        "sql": """SELECT date, value
FROM us_dollar_index
ORDER BY date DESC
LIMIT 20""",
        "market": "US"
    },
    {
        "category": "volatility",
        "question": "현재 시장 국면",
        "sql": """SELECT created_at, regime, vix_proxy, spy_return_1m, spy_return_3m, spy_ma200_distance
FROM us_market_regime
ORDER BY created_at DESC
LIMIT 1""",
        "market": "US"
    },
]

US_ETF_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "etf",
        "question": "SPY ETF 수익률",
        "sql": """SELECT date, close, volume
FROM us_daily_etf
WHERE symbol = 'SPY'
ORDER BY date DESC
LIMIT 10""",
        "market": "US"
    },
    {
        "category": "etf",
        "question": "주요 ETF 비교",
        "sql": """SELECT symbol, close, volume
FROM us_daily_etf
WHERE symbol IN ('SPY', 'QQQ', 'IWM', 'DIA') AND date = (SELECT MAX(date) FROM us_daily_etf)
ORDER BY close DESC""",
        "market": "US"
    },
]

US_TIME_SERIES_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "time_series",
        "question": "애플 주간 주가 추이",
        "sql": """SELECT date, open, high, low, close, volume
FROM us_weekly
WHERE symbol = 'AAPL'
ORDER BY date DESC
LIMIT 12""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "time_series",
        "question": "테슬라 월간 수익률",
        "sql": """SELECT date, open, close, (close - open) / open * 100 as monthly_return, volume
FROM us_monthly
WHERE symbol = 'TSLA'
ORDER BY date DESC
LIMIT 12""",
        "market": "US",
        "chart_indicators": True
    },
]


# =============================================================================
# BOTH MARKET EXAMPLES (KR + US Combined UNION Queries)
# =============================================================================

BOTH_MARKET_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "financial",
        "question": "한미 배당수익률 높은 주식 비교 10개",
        "sql": """(SELECT symbol, stock_name, dividend_yield, dps, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total) AND dividend_yield > 0
ORDER BY dividend_yield DESC LIMIT 5)
UNION ALL
(SELECT s.symbol, s.stock_name, s.dividendyield, s.dividendpershare, 'US' as market
FROM us_stock_basic s
WHERE s.dividendyield > 0
ORDER BY s.dividendyield DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    {
        "category": "technical",
        "question": "RSI 30 이하 과매도 종목",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, i.rsi, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE i.date = (SELECT MAX(date) FROM kr_indicators) AND i.rsi < 30
ORDER BY i.rsi ASC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, i.rsi, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators) AND i.rsi < 30
ORDER BY i.rsi ASC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    {
        "category": "ranking",
        "question": "거래량 상위 10개 종목",
        "sql": """(SELECT symbol, stock_name, close, volume, change_rate, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY volume DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, d.volume, d.change_rate, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY d.volume DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "매수 등급 종목",
        "sql": """(SELECT k.symbol, k.stock_name, g.final_grade, g.final_score, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND g.final_grade IN ('강력 매수', '매수', '매수 고려')
ORDER BY g.final_score DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, g.final_grade, g.final_score, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE d.date = (SELECT MAX(date) FROM us_daily)
  AND g.final_grade IN ('강력 매수', '매수', '매수 고려')
ORDER BY g.final_score DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    {
        "category": "sector",
        "question": "한미 반도체 관련주 RSI 30 이하 거래대금 상위 10개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, i.rsi, k.trading_value, d.industry, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
JOIN kr_stock_detail d ON k.symbol = d.symbol
WHERE i.date = (SELECT MAX(date) FROM kr_indicators) AND i.rsi < 30
  AND d.industry LIKE '%반도체%'
ORDER BY k.trading_value DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, b.stock_name, d.close, i.rsi, d.trading_value, b.industry, 'US' as market
FROM us_daily d
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
JOIN us_stock_basic b ON d.symbol = b.symbol
WHERE i.date = (SELECT MAX(date) FROM us_indicators) AND i.rsi < 30
  AND b.industry ILIKE '%semiconductor%'
ORDER BY d.trading_value DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
]

# =============================================================================
# NEW COVERAGE EXAMPLES (Gap-filling)
# =============================================================================

NEW_COVERAGE_EXAMPLES: List[Dict[str, str]] = [
    # --- US Financial Statement (3) ---
    {
        "category": "financial",
        "question": "테슬라 최근 분기별 매출과 순이익률 추이",
        "sql": """SELECT fiscal_date_ending, total_revenue, net_income,
  ROUND(net_income * 100.0 / NULLIF(total_revenue, 0), 2) as net_margin_pct
FROM us_income_statement
WHERE symbol = 'TSLA'
ORDER BY fiscal_date_ending DESC
LIMIT 8""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "financial",
        "question": "엔비디아 부채비율과 현금보유량",
        "sql": """SELECT fiscal_date_ending, total_assets, total_liabilities,
  cash_and_cash_equivalents_at_carrying_value as cash,
  ROUND(total_liabilities * 100.0 / NULLIF(total_shareholder_equity, 0), 2) as debt_ratio_pct,
  long_term_debt
FROM us_balance_sheet
WHERE symbol = 'NVDA'
ORDER BY fiscal_date_ending DESC
LIMIT 4""",
        "market": "US",
        "chart_indicators": True
    },
    # --- US Options + Earnings (2) ---
    {
        "category": "earnings",
        "question": "실적 발표 예정 종목 중 옵션 변동성 높은 종목",
        "sql": """SELECT e.symbol, e.name, e.reportdate, e.estimate,
  o.avg_implied_volatility, o.total_call_volume, o.total_put_volume,
  ROUND(o.total_put_volume::numeric / NULLIF(o.total_call_volume, 0), 2) as put_call_ratio
FROM us_earnings_calendar e
JOIN us_option_daily_summary o ON e.symbol = o.symbol
WHERE e.reportdate BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
  AND o.date = (SELECT MAX(date) FROM us_option_daily_summary)
  AND o.avg_implied_volatility > 40
ORDER BY o.avg_implied_volatility DESC
LIMIT 15""",
        "market": "US",
        "chart_indicators": True
    },
    # --- BOTH Market Advanced (3) ---
    {
        "category": "ranking",
        "question": "한미 반도체 종목 PER 비교",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, k.per, d.industry, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_detail d ON k.symbol = d.symbol
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND d.industry LIKE '%반도체%' AND k.per > 0
ORDER BY k.per ASC LIMIT 10)
UNION ALL
(SELECT d.symbol, b.stock_name, d.close, d.per, b.industry, 'US' as market
FROM us_daily d
JOIN us_stock_basic b ON d.symbol = b.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
  AND b.industry ILIKE '%semiconductor%' AND d.per > 0
ORDER BY d.per ASC LIMIT 10)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    {
        "category": "quant",
        "question": "한미 매수등급 RSI 40 이하 종목",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, g.final_grade, g.final_score, i.rsi, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND g.final_grade IN ('강력 매수', '매수', '매수 고려') AND i.rsi < 40
ORDER BY g.final_score DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, g.final_grade, g.final_score, i.rsi, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE d.date = (SELECT MAX(date) FROM us_daily)
  AND g.final_grade IN ('강력 매수', '매수', '매수 고려') AND i.rsi < 40
ORDER BY g.final_score DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    {
        "category": "sector",
        "question": "한미 바이오 업종 거래대금 상위 종목",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, k.trading_value, d.industry, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_detail d ON k.symbol = d.symbol
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND d.industry LIKE '%바이오%'
ORDER BY k.trading_value DESC LIMIT 10)
UNION ALL
(SELECT d.symbol, b.stock_name, d.close, d.trading_value, b.industry, 'US' as market
FROM us_daily d
JOIN us_stock_basic b ON d.symbol = b.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
  AND b.industry ILIKE '%biotech%'
ORDER BY d.trading_value DESC LIMIT 10)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # --- Macro + Equity (2) ---
    {
        "category": "macro",
        "question": "현재 연방기금금리와 가치점수 높은 종목",
        "sql": """SELECT g.symbol, s.stock_name, d.close, g.value_score, g.final_grade,
  (SELECT value FROM us_fed_funds_rate ORDER BY date DESC LIMIT 1) as current_fed_rate
FROM us_stock_grade g
JOIN us_stock_basic s ON g.symbol = s.symbol
JOIN us_daily d ON g.symbol = d.symbol AND d.date = (SELECT MAX(date) FROM us_daily)
WHERE g.date = (SELECT MAX(date) FROM us_stock_grade) AND g.value_score >= 70
ORDER BY g.value_score DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "macro",
        "question": "한국 기준금리 추이",
        "sql": """SELECT stat_name, item_name1, time_value, data_value, unit_name
FROM bok_economic_indicators
WHERE stat_name LIKE '%기준금리%' OR item_name1 LIKE '%기준금리%'
ORDER BY time_value DESC
LIMIT 12""",
        "market": "KR"
    },
    # --- Insider + Program Trading (2) ---
    {
        "category": "corporate_action",
        "question": "최근 30일 내부자 매수 많은 종목",
        "sql": """SELECT symbol, COUNT(*) as buy_count,
  SUM(shares) as total_shares,
  ROUND(AVG(share_price)::numeric, 2) as avg_price
FROM us_insider_transactions
WHERE acquisition_or_disposal = 'A'
  AND date >= (SELECT MAX(date) FROM us_insider_transactions) - INTERVAL '30 days'
GROUP BY symbol
HAVING COUNT(*) >= 2
ORDER BY total_shares DESC
LIMIT 20""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "investor",
        "question": "최근 프로그램 매매 순매수 추이",
        "sql": """SELECT date, category, buy_value, sell_value, net_buy_value
FROM kr_program_daily_trading
WHERE date >= (SELECT MAX(date) FROM kr_program_daily_trading) - INTERVAL '30 days'
ORDER BY date DESC, category""",
        "market": "KR"
    },
    # --- KR Research + Exchange Rate (2) ---
    {
        "category": "research",
        "question": "목표가 대비 현재가 괴리율 큰 종목",
        "sql": """SELECT r.stock_name, r.symbol, r.securities_firm, r.target_price,
  k.close as current_price,
  ROUND((r.target_price - k.close) * 100.0 / k.close, 2) as upside_pct,
  r.investment_opinion, r.date as report_date
FROM kr_research_reports r
JOIN kr_intraday_total k ON r.symbol = k.symbol
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND r.date >= (SELECT MAX(date) FROM kr_research_reports) - INTERVAL '30 days'
  AND r.target_price > k.close
ORDER BY upside_pct DESC
LIMIT 20""",
        "market": "KR",
        "chart_indicators": True
    },
    {
        "category": "macro",
        "question": "원달러 환율 추이",
        "sql": """SELECT time_value, data_value, item_name1, unit_name
FROM exchange_rate
WHERE item_name1 LIKE '%달러%' OR item_name1 LIKE '%USD%'
ORDER BY time_value DESC
LIMIT 30""",
        "market": "KR"
    },
]


# =============================================================================
# BOTH MARKET - BASIC PATTERNS (B-1: BOTH data augmentation, 20 examples)
# =============================================================================

BOTH_MARKET_BASIC_EXAMPLES: List[Dict[str, str]] = [
    # 1. RSI oversold 5 (KR=3, US=2)
    # 2. MACD golden cross 10 (KR=5, US=5)
    # 3. Volume top 7 (KR=4, US=3)
    # 4. Market cap top 3 (KR=2, US=1)
    {
        "category": "ranking",
        "question": "한미 시가총액 상위 3개",
        "sql": """(SELECT symbol, stock_name, close, market_cap, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY market_cap DESC LIMIT 2)
UNION ALL
(SELECT d.symbol, b.stock_name, d.close, b.market_cap, 'US' as market
FROM us_daily d
JOIN us_stock_basic b ON d.symbol = b.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY b.market_cap DESC LIMIT 1)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 5. Strong buy grade 10 (KR=5, US=5)
    # 6. Semiconductor comparison 5 (KR=3, US=2)
    # 7. RSI overbought 6 (KR=3, US=3)
    # 8. Momentum score top 8 (KR=4, US=4)
    {
        "category": "quant",
        "question": "한미 모멘텀점수 상위 8개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, g.momentum_score, g.final_grade, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND g.momentum_score >= 60
ORDER BY g.momentum_score DESC LIMIT 4)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, g.momentum_score, g.final_grade, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE d.date = (SELECT MAX(date) FROM us_daily)
  AND g.momentum_score >= 60
ORDER BY g.momentum_score DESC LIMIT 4)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 9. Decline rate top 5 (KR=3, US=2)
    # 10. Bollinger upper breakout 4 (KR=2, US=2)
    # 11. Low risk buy grade 10 (KR=5, US=5)
    {
        "category": "quant",
        "question": "한미 저위험 매수등급 종목 10개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, g.final_grade, g.final_score, g.risk_flag, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND g.final_grade IN ('강력 매수', '매수', '매수 고려') AND g.risk_flag = 'NORMAL'
ORDER BY g.final_score DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, g.final_grade, g.final_score, g.risk_flag, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE d.date = (SELECT MAX(date) FROM us_daily)
  AND g.final_grade IN ('강력 매수', '매수', '매수 고려') AND g.risk_flag = 'NORMAL'
ORDER BY g.final_score DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 12. Value score >= 70 6 (KR=3, US=3)
    # 13. MACD dead cross 8 (KR=4, US=4)
    # 14. SMA breakout 10 (KR=5, US=5)
    {
        "category": "technical",
        "question": "한미 이동평균선(KR 20일/US 13주) 돌파 종목 10개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, i.sma, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE i.date = (SELECT MAX(date) FROM kr_indicators) AND k.close > i.sma AND i.sma > 0
ORDER BY (k.close - i.sma) / i.sma DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, i.sma, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators) AND d.close > i.sma AND i.sma > 0
ORDER BY (d.close - i.sma) / i.sma DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 15. High conviction buy 5 (KR=3, US=2)
    # 16. Market cap top 20 (KR=10, US=10)
    # 17. Trading value top 5 (KR=3, US=2)
    # 18. Low PER undervalued 10 (KR=5, US=5)
    {
        "category": "ranking",
        "question": "한미 PER 낮은 저평가 종목 10개",
        "sql": """(SELECT symbol, stock_name, close, per, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total) AND per > 0
ORDER BY per ASC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, d.per, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily) AND d.per > 0
ORDER BY d.per ASC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 19. Rise rate top 4 (KR=2, US=2)
    # 20. High ATR volatile stocks 6 (KR=3, US=3)
    {
        "category": "technical",
        "question": "한미 변동성 높은 종목 6개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, i.atr, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE i.date = (SELECT MAX(date) FROM kr_indicators) AND i.atr > 0
ORDER BY i.atr DESC LIMIT 3)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, i.atr, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators) AND i.atr > 0
ORDER BY i.atr DESC LIMIT 3)""",
        "market": "BOTH",
        "chart_indicators": True
    },
]


# =============================================================================
# BOTH MARKET - SIMPLE SQL (B-3: prevent over-conditioning, 15 examples)
# Questions are simple -> SQL must be simple. No extra conditions beyond what is asked.
# =============================================================================

BOTH_SIMPLE_SQL_EXAMPLES: List[Dict[str, str]] = [
    # 1. Semiconductor stocks - industry filter only, no RSI/MACD/etc.
    {
        "category": "sector",
        "question": "한미 반도체 관련주 5개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, k.change_rate, det.industry, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_detail det ON k.symbol = det.symbol
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
  AND det.industry LIKE '%반도체%'
ORDER BY k.market_cap DESC LIMIT 3)
UNION ALL
(SELECT d.symbol, b.stock_name, d.close, d.change_rate, b.industry, 'US' as market
FROM us_daily d
JOIN us_stock_basic b ON d.symbol = b.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
  AND b.industry ILIKE '%semiconductor%'
ORDER BY b.market_cap DESC LIMIT 2)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 2. Show RSI - no range filter, just display
    {
        "category": "technical",
        "question": "한미 RSI 보여줘 10개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, i.rsi, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY k.volume DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, i.rsi, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators)
ORDER BY d.volume DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 3. High volume stocks 3 - just order by volume, nothing else
    # 4. Large market cap stocks 5 - no industry/grade filters
    # 5. Show MACD - no golden/dead cross filter
    {
        "category": "technical",
        "question": "한미 MACD 지표 보여줘 10개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, i.macd, i.macd_signal, i.macd_hist, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY k.volume DESC LIMIT 5)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, i.macd, i.macd_signal, i.macd_hist, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators)
ORDER BY d.volume DESC LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 6. High price stocks 4 - ORDER BY close only
    # 7. Buy grade stocks 5 - grade filter only, no extra score/risk threshold
    # 8. Show Bollinger Bands - display only, no breakout filter
    # 9. High trading value 6 - ORDER BY trading_value only
    # 10. Technical summary 5 - RSI+MACD without condition filtering
    # 11. Change rate check 5 - show change_rate, no threshold filter
    # 12. Large cap status 4 - market_cap order only
    # 13. Quant score comparison 5 - show scores without grade filter
    {
        "category": "quant",
        "question": "한미 퀀트 점수 비교 5개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, g.final_score, g.value_score, g.momentum_score, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_grade g ON k.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM kr_stock_grade)
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY g.final_score DESC LIMIT 3)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, g.final_score, g.value_score, g.momentum_score, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol AND g.date = (SELECT MAX(date) FROM us_stock_grade)
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY g.final_score DESC LIMIT 2)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 14. PER comparison 5 - show PER, no threshold
    # 15. RSI MACD comparison 8 - show both indicators, no conditions
]


# =============================================================================
# BOTH MARKET - EXPRESSION VARIANTS (diverse Korean expressions, 10 examples)
# Same UNION ALL pattern with different Korean expressions for "both markets"
# =============================================================================

BOTH_EXPRESSION_VARIANTS: List[Dict[str, str]] = [
    # 1. "한국 미국" expression
    {
        "category": "technical",
        "question": "한국 미국 RSI 과매도 종목 5개",
        "sql": """(SELECT k.symbol, k.stock_name, k.close, i.rsi, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE i.date = (SELECT MAX(date) FROM kr_indicators) AND i.rsi < 30
ORDER BY i.rsi ASC LIMIT 3)
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, i.rsi, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators) AND i.rsi < 30
ORDER BY i.rsi ASC LIMIT 2)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 2. "양국 시장" expression
    # 3. "한국과 미국" expression
    # 4. "KR US" expression
    {
        "category": "ranking",
        "question": "KR US 시가총액 상위 5개",
        "sql": """(SELECT symbol, stock_name, close, market_cap, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY market_cap DESC LIMIT 3)
UNION ALL
(SELECT d.symbol, b.stock_name, d.close, b.market_cap, 'US' as market
FROM us_daily d
JOIN us_stock_basic b ON d.symbol = b.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY b.market_cap DESC LIMIT 2)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 5. "코스피 나스닥" expression
    # 6. "국내외" expression
    # 7. "한미 양시장" expression
    # 8. "미국 한국" (reverse order) expression
    # 9. "글로벌" expression
    {
        "category": "ranking",
        "question": "글로벌 시가총액 상위 종목 5개",
        "sql": """(SELECT symbol, stock_name, close, market_cap, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY market_cap DESC LIMIT 3)
UNION ALL
(SELECT d.symbol, b.stock_name, d.close, b.market_cap, 'US' as market
FROM us_daily d
JOIN us_stock_basic b ON d.symbol = b.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY b.market_cap DESC LIMIT 2)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # 10. "내외국 주식" expression
]


# =============================================================================
# SECTOR / INDUSTRY / THEME EXAMPLES (10 examples)
# =============================================================================

SECTOR_INDUSTRY_THEME_EXAMPLES: List[Dict[str, str]] = [
    # US: industry for specific sub-industry (NOT sector)
    {
        "category": "sector",
        "question": "미국 반도체 관련주 시총 상위 10개",
        "sql": """SELECT b.symbol, b.stock_name, b.industry, b.market_cap
FROM us_stock_basic b
WHERE b.industry ILIKE '%SEMICONDUCTOR%'
ORDER BY b.market_cap DESC NULLS LAST
LIMIT 10""",
        "market": "US",
        "chart_indicators": True
    },
    {
        "category": "sector",
        "question": "미국 기술 섹터 종목 시총 상위 10개",
        "sql": """SELECT b.symbol, b.stock_name, b.sector, b.industry, b.market_cap
FROM us_stock_basic b
WHERE b.sector = 'TECHNOLOGY'
ORDER BY b.market_cap DESC NULLS LAST
LIMIT 10""",
        "market": "US",
        "chart_indicators": True
    },
    # KR: theme for "관련주" (broader coverage)
    {
        "category": "sector",
        "question": "한국 반도체 관련주 시총 상위 10개",
        "sql": """SELECT k.symbol, k.stock_name, k.close, k.market_cap, d.theme
FROM kr_intraday k
JOIN kr_stock_detail d ON k.symbol = d.symbol
WHERE d.theme = 'Semiconductor'
ORDER BY k.market_cap DESC NULLS LAST
LIMIT 10""",
        "market": "KR",
        "chart_indicators": True
    },
    # BOTH: KR theme + US industry UNION ALL
    {
        "category": "sector",
        "question": "한미 반도체 관련주 시총 상위 10개",
        "sql": """(SELECT k.symbol, k.stock_name, k.market_cap, 'KR' as market
FROM kr_intraday k
JOIN kr_stock_detail d ON k.symbol = d.symbol
WHERE d.theme = 'Semiconductor'
ORDER BY k.market_cap DESC NULLS LAST
LIMIT 5)
UNION ALL
(SELECT b.symbol, b.stock_name, b.market_cap, 'US' as market
FROM us_stock_basic b
WHERE b.industry ILIKE '%SEMICONDUCTOR%'
ORDER BY b.market_cap DESC NULLS LAST
LIMIT 5)""",
        "market": "BOTH",
        "chart_indicators": True
    },
    # US: legitimate sector usage (GROUP BY sector)
    {
        "category": "sector",
        "question": "미국 섹터별 종목 수와 평균 시총",
        "sql": """SELECT sector, COUNT(*) as stock_count, AVG(market_cap) as avg_market_cap
FROM us_stock_basic
WHERE sector IS NOT NULL AND sector NOT IN ('NONE', 'OTHER')
GROUP BY sector
ORDER BY avg_market_cap DESC""",
        "market": "US"
    },
]


# =============================================================================
# RECOMMENDATION EXAMPLES (Daily Buy Recommendations)
# =============================================================================

KR_RECOMMENDATION_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "recommendation",
        "question": "지금 뭐 사야 돼?",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, time_series_text, risk_profile_text,
       close, change_rate, volatility_annual, max_drawdown_1y,
       beta, sector_momentum, rs_value, rs_rank, industry_rank, sector_rank
FROM daily_recommendation
WHERE country = 'KR'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'KR')
ORDER BY rank ASC""",
        "market": "KR",
    },
    {
        "category": "recommendation",
        "question": "요즘 살만한 주식 있어?",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, time_series_text, risk_profile_text,
       close, change_rate, volatility_annual, max_drawdown_1y,
       beta, sector_momentum, rs_value, rs_rank, industry_rank, sector_rank
FROM daily_recommendation
WHERE country = 'KR'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'KR')
ORDER BY rank ASC""",
        "market": "KR",
    },
    {
        "category": "recommendation",
        "question": "오늘 매수 추천 종목 알려줘",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, close, change_rate, rs_rank, sector_momentum
FROM daily_recommendation
WHERE country = 'KR'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'KR')
ORDER BY rank ASC""",
        "market": "KR",
    },
    {
        "category": "recommendation",
        "question": "좋은 종목 추천해줘",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, time_series_text, close, change_rate, volatility_annual
FROM daily_recommendation
WHERE country = 'KR'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'KR')
ORDER BY rank ASC""",
        "market": "KR",
    },
    {
        "category": "recommendation",
        "question": "뭐 살까?",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, close, change_rate, rs_rank, sector_momentum
FROM daily_recommendation
WHERE country = 'KR'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'KR')
ORDER BY rank ASC""",
        "market": "KR",
    },
    {
        "category": "recommendation",
        "question": "어디에 투자하면 될까?",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, close, change_rate, rs_rank, sector_momentum
FROM daily_recommendation
WHERE country = 'KR'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'KR')
ORDER BY rank ASC""",
        "market": "KR",
    },
    {
        "category": "recommendation",
        "question": "괜찮은 종목 있어?",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, close, change_rate, rs_rank, sector_momentum
FROM daily_recommendation
WHERE country = 'KR'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'KR')
ORDER BY rank ASC""",
        "market": "KR",
    },
]

US_RECOMMENDATION_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "recommendation",
        "question": "미국 주식 뭐 살까?",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, time_series_text, risk_profile_text,
       close, change_rate, volatility_annual, max_drawdown_1y,
       beta, sector_momentum, rs_value, rs_rank, industry_rank, sector_rank
FROM daily_recommendation
WHERE country = 'US'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'US')
ORDER BY rank ASC""",
        "market": "US",
    },
    {
        "category": "recommendation",
        "question": "미국 추천 종목 알려줘",
        "sql": """SELECT stock_name, symbol, rank, final_grade, final_score,
       signal_overall, close, change_rate, rs_rank, sector_momentum
FROM daily_recommendation
WHERE country = 'US'
  AND date = (SELECT MAX(date) FROM daily_recommendation WHERE country = 'US')
ORDER BY rank ASC""",
        "market": "US",
    },
]


# =============================================================================
# STRATEGY EXAMPLES (Investment Strategy / Scenario)
# =============================================================================

KR_STRATEGY_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "strategy",
        "question": "삼성전자 투자 전략 시나리오",
        "sql": """SELECT g.symbol, g.stock_name, g.final_grade, g.final_score,
       g.scenario_bullish_prob, g.scenario_sideways_prob, g.scenario_bearish_prob,
       g.scenario_bullish_return, g.scenario_sideways_return, g.scenario_bearish_return,
       g.stop_loss_pct, g.take_profit_pct, g.risk_reward_ratio,
       g.entry_timing_score, g.position_size_pct,
       g.buy_triggers, g.sell_triggers, g.hold_triggers,
       g.signal_overall, g.market_state, g.risk_profile_text, g.risk_recommendation,
       k.close, k.change_rate, k.volume
FROM kr_stock_grade g
JOIN kr_intraday k ON g.symbol = k.symbol
WHERE g.symbol = '005930'
  AND g.date = (SELECT MAX(date) FROM kr_stock_grade)""",
        "market": "KR",
        "chart_indicators": True
    },
]

US_STRATEGY_EXAMPLES: List[Dict[str, str]] = [
    {
        "category": "strategy",
        "question": "테슬라 투자 전략 시나리오",
        "sql": """SELECT g.symbol, g.stock_name, g.final_grade, g.final_score,
       g.scenario_bullish_prob, g.scenario_sideways_prob, g.scenario_bearish_prob,
       g.scenario_bullish_return, g.scenario_sideways_return, g.scenario_bearish_return,
       g.stop_loss_pct, g.take_profit_pct, g.risk_reward_ratio,
       g.entry_timing_score, g.position_size_pct,
       g.buy_triggers, g.sell_triggers, g.hold_triggers,
       g.signal_overall, g.market_state, g.risk_profile_text,
       d.close, d.change_rate, d.volume
FROM us_stock_grade g
JOIN us_daily d ON g.symbol = d.symbol AND d.date = (SELECT MAX(date) FROM us_daily WHERE symbol = g.symbol)
WHERE g.symbol = 'TSLA'
  AND g.date = (SELECT MAX(date) FROM us_stock_grade)""",
        "market": "US",
        "chart_indicators": True
    },
]


# =============================================================================
# COMBINED FEW-SHOT EXAMPLES
# =============================================================================



FEW_SHOT_EXAMPLES: List[Dict[str, str]] = (
    # KR Examples (Original)
    KR_SIMPLE_QUERY_EXAMPLES +               # 2
    KR_RANKING_EXAMPLES +                    # 4
    KR_FILTER_EXAMPLES +                     # 3
    KR_TECHNICAL_EXAMPLES +                  # 5
    KR_COMPLEX_EXAMPLES +                    # 2
    KR_INVESTOR_EXAMPLES +                   # 3
    KR_QUANT_EXAMPLES +                      # 6
    KR_MARKET_EXAMPLES +                     # 2
    KR_CTE_EXAMPLES +                        # 6
    KR_SCREENING_EXAMPLES +                  # 2
    KR_TIME_SERIES_EXAMPLES +                # 7
    KR_WINDOW_FUNCTION_EXAMPLES +            # 4
    KR_CASE_WHEN_EXAMPLES +
    KR_ADVANCED_JOIN_EXAMPLES +              # 3
    KR_DIVERGENT_EXAMPLES +                  # 3
    # KR Examples (New)
    KR_FINANCIAL_EXAMPLES +                  # 5
    KR_SECTOR_EXAMPLES +
    KR_CORPORATE_ACTION_EXAMPLES +
    KR_OWNERSHIP_EXAMPLES +                  # 1
    KR_RESEARCH_EXAMPLES +                   # 3
    KR_ANALYSIS_EXAMPLES +                   # 2
    # US Examples (Original)
    US_SIMPLE_QUERY_EXAMPLES +               # 1
    US_RANKING_EXAMPLES +                    # 2
    US_TECHNICAL_EXAMPLES +                  # 1
    US_MARKET_EXAMPLES +                     # 3
    US_MACRO_EXAMPLES +                      # 5
    # US Examples (New)
    US_FINANCIAL_EXAMPLES +
    US_EARNINGS_EXAMPLES +
    US_OPTIONS_EXAMPLES +                    # 2
    US_CORPORATE_ACTION_EXAMPLES +
    US_NEWS_EXAMPLES +                       # 1
    US_QUANT_EXAMPLES +                      # 3
    US_SECTOR_EXAMPLES +                     # 5
    US_VOLATILITY_EXAMPLES +                 # 4
    US_ETF_EXAMPLES +                        # 2
    US_TIME_SERIES_EXAMPLES +                # 2
    US_ANALYSIS_EXAMPLES +                   # 2
    # BOTH Market Examples (Original)
    BOTH_MARKET_EXAMPLES +                   # 5
    # BOTH Market Examples (B-1: augmentation, B-3: simple SQL)
    BOTH_MARKET_BASIC_EXAMPLES +             # 6
    BOTH_SIMPLE_SQL_EXAMPLES +               # 4
    BOTH_EXPRESSION_VARIANTS +               # 3
    # Coverage gap-filling examples
    NEW_COVERAGE_EXAMPLES +
    # Sector/Industry/Theme examples
    SECTOR_INDUSTRY_THEME_EXAMPLES +
    # Recommendation examples (daily buy picks)
    KR_RECOMMENDATION_EXAMPLES +             # 7
    US_RECOMMENDATION_EXAMPLES +             # 2
    # Strategy examples (investment scenario)
    KR_STRATEGY_EXAMPLES +                   # 1
    US_STRATEGY_EXAMPLES              # 1
)  # Total: 153 examples


def get_few_shot_examples(
    category: Optional[str] = None,
    market: str = "KR",
    limit: int = 5
) -> List[Dict[str, str]]:
    """
    Get few-shot examples filtered by category and market

    Args:
        category: Filter by category (ranking, filter, technical, etc.)
        market: 'KR', 'US', or 'BOTH'
        limit: Maximum number of examples

    Returns:
        List of example dictionaries
    """
    filtered = FEW_SHOT_EXAMPLES

    # Filter by market
    if market:
        if market == "BOTH":
            # For BOTH market, return BOTH examples primarily
            filtered = [ex for ex in filtered if ex.get("market") == "BOTH"]
        else:
            filtered = [ex for ex in filtered if ex.get("market") == market]

    # Filter by category
    if category:
        filtered = [ex for ex in filtered if ex.get("category") == category]

    return filtered[:limit]


def get_similar_examples(
    intent: str,
    market: str = "KR",
    limit: int = 3
) -> List[Dict[str, str]]:
    """
    Get similar examples based on intent

    Args:
        intent: User intent (query, ranking, filter, analysis, etc.)
        market: 'KR', 'US', or 'BOTH'
        limit: Maximum number of examples

    Returns:
        List of similar examples
    """
    # Map intent to category
    intent_to_category = {
        "query": "simple_query",
        "ranking": "ranking",
        "filter": "filter",
        "technical": "technical",
        "analysis": "analysis",
        "comparison": "analysis",
        "investor": "investor",
        "quant": "quant",
        "market": "market",
        "macro": "macro",
        # SQL patterns
        "cte": "cte",
        "time_series": "time_series",
        "window": "window_function",
        "classification": "case_when",
        "advanced": "advanced_join",
        # Divergent/opposite pattern
        "divergent": "divergent",
        "opposite": "divergent",
        "extreme": "divergent",
        # Financial / Corporate (NEW)
        "financial": "financial",
        "dividend": "financial",
        "earnings": "earnings",
        "income": "financial",
        "balance": "financial",
        "cashflow": "financial",
        # Sector (NEW)
        "sector": "sector",
        "industry": "sector",
        "theme": "sector",
        "benchmark": "sector",
        # Corporate action (NEW)
        "corporate_action": "corporate_action",
        "ipo": "corporate_action",
        "split": "corporate_action",
        "insider": "corporate_action",
        "blocktrade": "corporate_action",
        # Ownership (NEW)
        "ownership": "ownership",
        "foreign_ownership": "ownership",
        # Research (NEW)
        "research": "research",
        "analyst": "research",
        "report": "research",
        # Options (NEW)
        "options": "options",
        "put_call": "options",
        # Volatility (NEW)
        "volatility": "volatility",
        "vix": "volatility",
        "regime": "volatility",
        # ETF (NEW)
        "etf": "etf",
    }

    category = intent_to_category.get(intent, "simple_query")
    return get_few_shot_examples(category=category, market=market, limit=limit)


def format_few_shot_for_prompt(examples: List[Dict[str, str]]) -> str:
    """
    Format few-shot examples for inclusion in prompt

    Args:
        examples: List of example dictionaries

    Returns:
        Formatted string for prompt
    """
    if not examples:
        return "No examples available."

    formatted = []
    for i, ex in enumerate(examples, 1):
        formatted.append(f"""Example {i}:
Question: {ex['question']}
SQL:
```sql
{ex['sql']}
```
""")
    return "\n".join(formatted)


# Example count verification
TOTAL_EXAMPLES = len(FEW_SHOT_EXAMPLES)
# Expected: 148 examples (deduplicated from 231)
# KR: 62 (after removing 30 SQL-pattern duplicates)
# US: 40 (after removing 10 SQL-pattern duplicates)
# BOTH: 18 (after removing 35 SQL-pattern duplicates)
# Other: 28 (Coverage: 12, Sector/Theme: 5, Strategy: 2)
