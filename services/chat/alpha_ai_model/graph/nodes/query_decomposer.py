# services/chat/alpha_ai_model/graph/nodes/query_decomposer.py
"""
Query Decomposer Node

Replaces: unified_classifier + entity_extractor + data_source_router + SchemaRAG table selection
in a single LLM call. Decomposes user query into sub-queries with explicit table assignments.

Feature flag: USE_QUERY_DECOMPOSITION (default: False)
"""
from typing import Dict, Any, List, Optional
import re
import json as json_module
from config import logger
from core.llm.factory import get_llm, LLMProvider

from langchain_core.messages import HumanMessage, AIMessage

from ...rag import QueryExpander
from ...stock_resolver import StockResolver, Market


# Accepted match methods for StockResolver (same as entity_extractor/unified_classifier)
ACCEPTED_MATCH_METHODS = {"exact", "alias", "partial"}
AI_RESPONSE_MATCH_METHODS = {"exact"}

# Hybrid detection keywords
HYBRID_KEYWORDS = [
    "분석", "전략", "추천", "제안", "포지션", "손절", "익절",
    "사이징", "유리한지", "어떤지", "비교", "감안", "전망",
    "리스크", "위험", "평가", "의견",
    # Investment judgment questions
    "사도돼", "사도될까", "살까", "살만", "사야", "매수해도", "들어가도", "진입",
    "오를까", "오르나", "올라갈까",
    "팔아도", "팔까", "팔아야", "매도해도",
    "내릴까", "내리나", "떨어질까", "빠질까",
    "괜찮을까", "어떨까", "전망이", "향후",
    "목표가", "손절가", "시나리오",
]

# External-only keywords
EXTERNAL_ONLY_KEYWORDS = [
    "뉴스", "news", "기사", "공시", "disclosure",
]

DECOMPOSITION_PROMPT = """You are a stock data query analyzer and decomposer.
Analyze the user's question and break it into sub-queries that can each be answered with a single SQL query.

## Available Tables

### KR Tables (Korean Market)
- kr_intraday_total: Daily price data (symbol, date, stock_name, exchange, close, open, high, low, volume, trading_value, market_cap, change_rate, per, pbr, roe, eps, dps, dividend_yield)
- kr_indicators: Technical indicators (symbol, date, stock_name, rsi, macd, macd_signal, macd_hist, real_upper_band, real_middle_band, real_lower_band, sma, ema, wma, adx, mfi, obv, atr, vwap, slowk, slowd, cci, roc, aroon)
- kr_stock_grade: Quant grades & investment strategy (symbol, date, stock_name, final_grade, final_score, value_score, quality_score, momentum_score, growth_score, confidence_score, var_95, sharpe_ratio, volatility_annual, beta, max_drawdown_1y, entry_timing_score, stop_loss_pct, take_profit_pct, risk_reward_ratio, position_size_pct, scenario_bullish_prob, scenario_sideways_prob, scenario_bearish_prob, scenario_bullish_return, scenario_sideways_return, scenario_bearish_return, buy_triggers, sell_triggers, hold_triggers, signal_overall, market_state, risk_profile_text, risk_recommendation). Scenario columns contain probability (%) and expected return ranges. Triggers are JSONB arrays of Korean condition strings. For investment strategy questions ("사도돼?", "오를까?"), SELECT scenario/trigger/stop_loss/take_profit columns
- kr_individual_investor_daily_trading: Investor trading (date, symbol, foreign_net_volume, foreign_net_value, inst_net_volume, inst_net_value, retail_net_volume, retail_net_value)
- kr_stock_detail: Stock info (symbol, stock_name, exchange, industry, theme, ceo_name)
- kr_stock_basic: Basic info (symbol, stock_name, stock_name_eng, listed_date, exchange)
- kr_financial_position: Financial statements - pivot table with account rows (symbol, stock_name, sj_div, account_nm, thstrm_amount, frmtrm_amount, bfefrmtrm_amount, bsns_year, fs_div, thstrm_nm). CRITICAL: Use fs_div='CFS' for consolidated statements (required for conglomerates like Samsung). Filter by sj_div='IS' for income items. For annual-only data, add: thstrm_nm NOT LIKE '%분기%' AND thstrm_nm NOT LIKE '%반기%'. Always GROUP BY or DISTINCT on symbol to avoid duplicates
- kr_dividends: Dividend/capital changes (symbol, corp_name, se, stock_knd, thstrm, frmtrm, lwfr, stlm_dt). se=event type, thstrm=current period amount
- kr_research_reports: Reports (symbol, stock_name, title, securities_firm, date, target_price, investment_opinion, summary)
- kr_foreign_ownership: Foreign ownership (symbol, stock_name, foreign_rate, foreign_rate_limit, foreign_ownership, date)
- kr_blocktrades: Block trades (symbol, stock_name, close, volume, block_volume, block_volume_rate, date)
- kr_largest_shareholder: Largest shareholder (symbol, corp_name, nm, relate, trmend_posesn_stock_co, trmend_posesn_stock_qota_rt, stlm_dt)
- kr_executive: Executives (symbol, corp_name, nm, ofcps, chrg_job, main_career, stlm_dt)
- kr_benchmark_index: Benchmark index (index_name, date, close, change_rate, open, high, low, volume)
- mv_sector_daily_performance: KR sector performance (date, sector_code, avg_return_30d, stock_count, sector_rank)

### US Tables (US Market)
- us_daily: Daily price data (symbol, date, close, open, high, low, volume, change_rate, per, pbr, trading_value)
- us_stock_basic: Stock info + fundamentals (symbol, stock_name, sector, industry, market_cap, per, eps, ebitda, dividendyield, analysttargetprice, forwardpe, pricetobookratio, pricetosalesratiottm, evtoebitda, operatingmarginttm, returnonequityttm, beta, week52high, week52low)
- us_indicators: Technical indicators (symbol, date, rsi, macd, macd_signal, macd_hist, real_upper_band, real_middle_band, real_lower_band, sma, ema, adx, mfi, atr, vwap, slowk, slowd)
- us_stock_grade: Quant grades & investment strategy (symbol, date, stock_name, final_grade, final_score, value_score, quality_score, momentum_score, growth_score, var_95, sharpe_ratio, volatility_annual, beta, entry_timing_score, stop_loss_pct, take_profit_pct, risk_reward_ratio, position_size_pct, scenario_bullish_prob, scenario_sideways_prob, scenario_bearish_prob, scenario_bullish_return, scenario_sideways_return, scenario_bearish_return, buy_triggers, sell_triggers, hold_triggers, signal_overall, market_state, risk_profile_text). For investment strategy questions, SELECT scenario/trigger/stop_loss/take_profit columns
- us_option: Options chain (symbol, date, type, strike, expiration, last, implied_volatility, delta, gamma, theta, vega, volume, open_interest)
- us_option_daily_summary: Options summary (symbol, date, total_call_volume, total_put_volume, avg_implied_volatility, net_gex, call_gex, put_gex, gex_ratio). Note: put_call_ratio must be calculated as total_put_volume / NULLIF(total_call_volume, 0)
- us_income_statement: Income statement (symbol, fiscal_date_ending, total_revenue, gross_profit, operating_income, net_income, ebit, ebitda)
- us_balance_sheet: Balance sheet (symbol, fiscal_date_ending, total_assets, total_liabilities, total_shareholder_equity, cash_and_cash_equivalents_at_carrying_value, short_long_term_debt_total)
- us_cash_flow: Cash flow (symbol, fiscal_date_ending, operating_cashflow, cashflow_from_investment, cashflow_from_financing, capital_expenditures, dividend_payout, net_income)
- us_earnings_estimates: Earnings estimates (symbol, estimate_date, horizon, eps_estimate_average, eps_estimate_low, eps_estimate_high, eps_estimate_revision_up_trailing_30_days, eps_estimate_revision_down_trailing_30_days, revenue_estimate_average)
- us_earnings_calendar: Earnings calendar (symbol, name, reportdate, fiscaldateending, estimate)
- us_dividends: Dividends (symbol, ex_dividend_date, amount, payment_date)
- us_splits: Stock splits (symbol, effective_date, split_factor)
- us_news: News (ticker, time_published, title, source, summary, overall_sentiment_score, overall_sentiment_label)
- us_insider_transactions: Insider transactions (symbol, date, executive, executive_title, acquisition_or_disposal, shares, share_price)
- us_ipo_calendar: IPO calendar (symbol, name, ipodate, priceRangeLow, priceRangeHigh, exchange)
- us_fed_funds_rate: Fed funds rate (date, value, name)
- us_treasury_yield: Treasury yield (date, value, name). Filter by name for maturity (e.g., '10-Year Treasury Constant Maturity Rate')
- us_cpi: CPI (date, value, name)
- us_unemployment_rate: Unemployment rate (date, value, name)
- us_gdp: GDP (date, value, name)
- us_pmi: PMI (date, value, name)
- us_vix: VIX (date, value, name)
- us_market_regime: Market regime (regime, vix_proxy, put_call_ratio, iv_skew, spy_return_1m, spy_return_3m, created_at)
- us_move_index: MOVE bond volatility (date, value)
- us_dollar_index: Dollar index (date, value)
- us_credit_spread: Credit spread (date, value, name)
- us_fed_rrp: Fed reverse repo (date, value)
- us_sector_benchmarks: Sector benchmarks (sector, date, pe_median, forward_pe_median, ps_median, ev_ebitda_median, operating_margin_median, roe_median, revenue_growth_median, eps_growth_median)
- us_daily_etf: ETF daily (symbol, date, open, high, low, close, volume)
- mv_us_sector_daily_performance: US sector performance (date, sector_code, avg_return_30d, stock_count, sector_rank)

### Common Tables
- market_index: Market index (exchange, date, close, change_rate, volume, open, high, low, trading_value) - KOSPI/KOSDAQ/NASDAQ/NYSE
- bok_economic_indicators: Korean economic indicators (stat_name, time_value, data_value, item_name1, unit_name). Filter by stat_name for indicator type
- exchange_rate: Exchange rate (item_name1, time_value, data_value, stat_name, unit_name). item_name1=currency pair name
- daily_recommendation: Daily curated stock buy recommendations (stock_name, symbol, date, country, rank, final_grade, final_score, signal_overall, time_series_text, risk_profile_text, close, change_rate, volatility_annual, max_drawdown_1y, beta, sector_momentum, rs_value, rs_rank, industry_rank, sector_rank). Filter by country='KR' or 'US'. Use date=(SELECT MAX(date) FROM daily_recommendation WHERE country='...'). ORDER BY rank ASC. Use this table for general buy recommendation questions WITHOUT a specific stock name (e.g., "뭐 살까?", "추천 종목", "뭐 사면 돼?", "어디에 투자할까?", "투자할 곳", "괜찮은 종목", "좋은 종목", "살만한 주식"). Budget/amount mentions (500만원, 오백만원, 천만원, 1억 등) do not change table selection. Do NOT use for specific stock questions like "삼성전자 사도돼?" - use kr_stock_grade/us_stock_grade instead.

## Classification Rules
Intent: chat, explain, query, ranking, filter, technical, investor, quant, market, analysis
Market: KR (Korean stocks/economy), US (US stocks/macro), BOTH (explicitly mentions both, or global keywords like 전세계, 세계, 글로벌)
Data Source:
- db_only: Pure quantitative/numerical data queries
- hybrid: Data + analytical advice (keywords: "분석", "전략", "추천", "제안", "포지션", "손절", "익절", "사이징", "유리한지", "어떤지")
- external_only: News/disclosure/web search only

## Derived Metrics Guide (CRITICAL - read before table selection)
Some metrics are NOT stored as columns and must be CALCULATED from multiple tables:
- EV/EBITDA: Use us_stock_basic.evtoebitda directly. Or calculate: us_balance_sheet (short_long_term_debt_total, cash_and_cash_equivalents_at_carrying_value) + us_income_statement (ebitda) + us_stock_basic (market_cap)
- PSR (Price/Sales): Use us_stock_basic.pricetosalesratiottm directly. Or calculate: us_stock_basic (market_cap) / us_income_statement (total_revenue)
- Operating Margin: Use us_stock_basic.operatingmarginttm directly. Or calculate: operating_income / total_revenue (both in us_income_statement)
- ROE: Use us_stock_basic.returnonequityttm directly. Or calculate: net_income (us_income_statement) / total_shareholder_equity (us_balance_sheet)
- IV Percentile: Use avg_implied_volatility from us_option_daily_summary as proxy (no pre-calculated percentile)
- Put/Call Ratio: Calculate total_put_volume / NULLIF(total_call_volume, 0) from us_option_daily_summary (no pre-calculated column)
- KR Sector Average PER: No kr_sector_benchmarks table. Use SQL subquery within a SINGLE sub-query: WHERE t.per < (SELECT AVG(t2.per) FROM kr_intraday_total t2 JOIN kr_stock_detail d2 ON t2.symbol = d2.symbol WHERE d2.industry = d.industry AND t2.date = t.date AND t2.per IS NOT NULL). Do NOT split into "calculate average" + "filter" sub-queries
- KR Operating Profit: kr_financial_position WHERE account_nm = '영업이익' AND sj_div='IS' AND fs_div='CFS' AND thstrm_nm NOT LIKE '%분기%' AND thstrm_nm NOT LIKE '%반기%'. Use thstrm_amount for current period. For YoY comparison, compare thstrm_amount vs frmtrm_amount
- US Financial Statements (CRITICAL): us_income_statement, us_balance_sheet, us_cash_flow contain ADR companies reporting in local currencies (KRW, JPY, ARS, etc.). ALWAYS add WHERE reported_currency = 'USD' when comparing financial figures across companies (ranking, sorting, filtering by amount). Without this filter, Korean/Japanese ADR values in KRW/JPY will appear as top results due to larger nominal numbers

## Decomposition Rules
1. Each sub-query should be answerable with ONE simple SQL query (max 3 JOINs)
2. Assign exact table names from the list above. Include ALL tables needed for derived metrics (see guide above)
3. If a sub-query needs results from another, mark depends_on with that sub-query's index (0-based)
4. For simple questions, return exactly 1 sub-query
5. Maximum 7 sub-queries per request
6. Each sub-query gets its own market (KR or US, not BOTH)
7. Analytical/strategic questions (strategy, position sizing, recommendations) should be answered by the LLM using SQL data, not by SQL itself. Set DATA_SOURCE to "hybrid" for such queries.
8. NEVER split aggregate comparison conditions into separate sub-queries. When filtering stocks by comparing against a group average (e.g., "PER below industry average", "volatility below market average"), use SQL subquery/CTE within ONE sub-query. WRONG: sub-query A "Calculate industry average PER" + sub-query B "Filter stocks below average" (depends_on A). CORRECT: Single sub-query using WHERE per < (SELECT AVG(per) FROM ... WHERE industry = ...). See Example 2.
9. SCREENING QUERIES: When the user asks to FIND/FILTER stocks matching multiple conditions simultaneously (keywords: "찾아줘", "필터링", "스크리닝", "이고", "이면서", "하고"), merge ALL filtering conditions into a SINGLE sub-query. The SQL generator will use CTEs to handle multi-table conditions in one query. WRONG: split "PER below average AND RSI 30-50 AND profit growth" into 3 independent sub-queries. CORRECT: ONE sub-query listing ALL required tables with all conditions described. Only create SEPARATE dependent sub-queries for ENRICHMENT data (investor trading, block trades) that requires the filtered result set.
10. For simple single-entity queries (e.g., "삼성전자 주가", "RSI 30 이하 종목", "거래량 상위 10"), generate exactly 1 sub-query. Do not over-decompose when a single SQL query suffices.

## Follow-up Detection
Determine if the user's query omits a subject/entity that must be inferred from conversation history.

Rules:
- IS_FOLLOW_UP=true: The query omits a stock name or entity that must be inferred from conversation history. Provide REWRITTEN_QUERY as a self-contained version.
- IS_FOLLOW_UP=false: The query is self-contained. Either it has its own stock name/entity, or it asks about a general topic (market, sector, index).
- If there is NO conversation history, IS_FOLLOW_UP is always false.

Decision examples:
- Previous: "삼성전자 사도돼?" / Current: "RSI는 몇이야?" -> IS_FOLLOW_UP=true, REWRITTEN_QUERY="삼성전자의 RSI는 몇이야?" (subject omitted)
- Previous: "삼성전자 사도돼?" / Current: "미투온 사도돼?" -> IS_FOLLOW_UP=false (new stock "미투온" present)
- Previous: "삼성전자 사도돼?" / Current: "시장 평균 RSI는?" -> IS_FOLLOW_UP=false (explicit subject "시장 평균")
- Previous: "삼성전자 사도돼?" / Current: "거기 PER은?" -> IS_FOLLOW_UP=true, REWRITTEN_QUERY="삼성전자의 PER은?" (deictic "거기")
- Previous: "삼성전자 사도돼?" / Current: "현재가?" -> IS_FOLLOW_UP=true, REWRITTEN_QUERY="삼성전자 현재가?" (minimal, subject omitted)
- No history / Current: "RSI는 몇이야?" -> IS_FOLLOW_UP=false (no history)
- Previous: "AAPL 어때?" / Current: "PER은?" -> IS_FOLLOW_UP=true, REWRITTEN_QUERY="AAPL의 PER은?"

## Few-shot Decomposition Examples

### Example 1: Cross-market + Quant + Macro
Question: "한국 종목 중 외국인+기관 순매수, 변동성 시장평균 이하, 시총 top5의 VaR/샤프 비교 + 한국 기준금리, 미국 금리/CPI/VIX 감안 분석"
INTENT: analysis
MARKET: BOTH
DATA_SOURCE: hybrid
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": 5, "order_by": "market_cap", "order_direction": "DESC"}}
SUB_QUERIES:
[
  {{"question": "최근 30일 외국인+기관 순매수이고 변동성이 시장평균 이하인 종목 중 시가총액 top 5와 VaR, 샤프비율", "market": "KR", "tables": ["kr_individual_investor_daily_trading", "kr_stock_grade", "kr_intraday_total"], "depends_on": null}},
  {{"question": "현재 한국 기준금리", "market": "KR", "tables": ["bok_economic_indicators"], "depends_on": null}},
  {{"question": "현재 미국 연방금리", "market": "US", "tables": ["us_fed_funds_rate"], "depends_on": null}},
  {{"question": "최근 미국 CPI 추이", "market": "US", "tables": ["us_cpi"], "depends_on": null}},
  {{"question": "현재 VIX 지수", "market": "US", "tables": ["us_vix"], "depends_on": null}}
]

### Example 2: Multi-condition screening (CRITICAL - conditions in SINGLE sub-query)
Question: "PER 업종평균 이하, 영업이익 YoY 증가, RSI 30-50, MACD 양전환 종목 중 목표가 괴리율 top5 + 투자자 매매/대량매매"
INTENT: analysis
MARKET: KR
DATA_SOURCE: hybrid
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": ["rsi", "macd"], "conditions": {{"rsi": {{"op": "BETWEEN", "value": [30, 50]}}}}, "time_range": null, "limit": 5, "order_by": null, "order_direction": null}}
SUB_QUERIES:
[
  {{"question": "PER이 업종평균 이하이고 영업이익 전년동기 대비 증가하고 RSI 30-50이며 MACD 양전환된 종목 중 목표가 괴리율 상위 5개를 CTE로 조회", "market": "KR", "tables": ["kr_intraday_total", "kr_indicators", "kr_stock_detail", "kr_financial_position", "kr_research_reports"], "depends_on": null}},
  {{"question": "상위 5개 종목의 기관/외국인/개인 순매수 동향", "market": "KR", "tables": ["kr_individual_investor_daily_trading"], "depends_on": 0}},
  {{"question": "상위 5개 종목의 대량매매 현황", "market": "KR", "tables": ["kr_blocktrades"], "depends_on": 0}}
]

### Example 3: US Options + Macro Regime + Earnings + Sector Benchmark
Question: "옵션 고IV + P/C비율 1.0이상 + EPS 상향 종목의 섹터벤치마크 대비 밸류에이션, 수익성, GEX, 시장레짐/신용스프레드/달러인덱스 감안 전략"
INTENT: analysis
MARKET: US
DATA_SOURCE: hybrid
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": ["iv", "put_call_ratio", "gex"], "conditions": {{"put_call_ratio": {{"op": ">=", "value": 1.0}}}}, "time_range": null, "limit": null, "order_by": null, "order_direction": null}}
SUB_QUERIES:
[
  {{"question": "IV가 높고 Put/Call 비율 1.0 이상인 종목 필터링", "market": "US", "tables": ["us_option_daily_summary"], "depends_on": null}},
  {{"question": "최근 30일 EPS 추정치 상향 조정된 종목", "market": "US", "tables": ["us_earnings_estimates"], "depends_on": null}},
  {{"question": "필터링된 종목의 PER, EV/EBITDA, PSR 밸류에이션과 영업이익률, ROE 수익성", "market": "US", "tables": ["us_stock_basic", "us_income_statement", "us_balance_sheet"], "depends_on": 0}},
  {{"question": "필터링된 종목의 섹터 벤치마크 대비 비교", "market": "US", "tables": ["us_sector_benchmarks"], "depends_on": 0}},
  {{"question": "필터링된 종목의 최근 GEX 추이", "market": "US", "tables": ["us_option_daily_summary"], "depends_on": 0}},
  {{"question": "현재 시장 레짐, 신용 스프레드, 달러 인덱스", "market": "US", "tables": ["us_market_regime", "us_credit_spread", "us_dollar_index"], "depends_on": null}}
]

### Example 4: Cross-market financial ranking (global operating income)
Question: "전세계 기업 중 연간 영업이익 상위 10개 나열해줘"
INTENT: ranking
MARKET: BOTH
DATA_SOURCE: db_only
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": "last_year", "limit": 10, "order_by": "operating_income", "order_direction": "DESC"}}
SUB_QUERIES:
[
  {{"question": "최근 연간 영업이익 상위 10개 미국 기업 (reported_currency='USD' 필터 필수)", "market": "US", "tables": ["us_income_statement", "us_stock_basic"], "depends_on": null}},
  {{"question": "최근 연간 영업이익 상위 10개 한국 기업", "market": "KR", "tables": ["kr_financial_position", "kr_stock_basic"], "depends_on": null}}
]

### Example 5: Currency conversion request
Question: "미국 시총 상위 5개 기업 원화로 알려줘"
INTENT: ranking
MARKET: US
DATA_SOURCE: db_only
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": 5, "order_by": "market_cap", "order_direction": "DESC"}}
SUB_QUERIES:
[
  {{"question": "미국 시가총액 상위 5개 기업", "market": "US", "tables": ["us_stock_basic"], "depends_on": null}},
  {{"question": "최신 원/달러 환율", "market": "KR", "tables": ["exchange_rate"], "depends_on": null}}
]

### Example 6: Single stock investment strategy question
Question: "삼성전자 사도돼? 지금 들어가도 될까?"
INTENT: analysis
MARKET: KR
DATA_SOURCE: hybrid
STOCK_SCOPE: specific
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": ["삼성전자"], "stock_codes": ["005930"], "indicators": [], "conditions": {{}}, "time_range": null, "limit": null, "order_by": null, "order_direction": null}}
SUB_QUERIES:
[
  {{"question": "삼성전자의 퀀트 등급, 시나리오별 확률/수익률, 손절가, 목표가, 매수/매도 트리거, 진입타이밍점수, 포지션비중, 리스크프로파일, 종합신호", "market": "KR", "tables": ["kr_stock_grade"], "depends_on": null}},
  {{"question": "삼성전자 현재가, RSI, MACD, ADX, 볼린저밴드", "market": "KR", "tables": ["kr_intraday_total", "kr_indicators"], "depends_on": null}}
]

### Example 7: Simple single-stock query (1 sub-query)
Question: "삼성전자 현재 주가"
INTENT: query
MARKET: KR
DATA_SOURCE: db_only
STOCK_SCOPE: specific
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": ["삼성전자"], "stock_codes": ["005930"], "indicators": [], "conditions": {{}}, "time_range": null, "limit": null, "order_by": null, "order_direction": null}}
SUB_QUERIES:
[
  {{"question": "삼성전자 현재 주가 (종가, 등락률, 거래량)", "market": "KR", "tables": ["kr_intraday_total"], "depends_on": null}}
]

### Example 8: Simple ranking query (1 sub-query)
Question: "거래량 상위 10 종목"
INTENT: ranking
MARKET: KR
DATA_SOURCE: db_only
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": 10, "order_by": "volume", "order_direction": "DESC"}}
SUB_QUERIES:
[
  {{"question": "최근 거래일 거래량 상위 10개 종목", "market": "KR", "tables": ["kr_intraday_total"], "depends_on": null}}
]

### Example 9: General buy recommendation (no specific stock)
Question: "뭐 살까?"
INTENT: query
MARKET: KR
DATA_SOURCE: hybrid
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": null, "order_by": "rank", "order_direction": "ASC"}}
SUB_QUERIES:
[
  {{"question": "오늘 매수 추천 종목", "market": "KR", "tables": ["daily_recommendation"], "depends_on": null}}
]

### Example 10: Investment recommendation with budget
Question: "500만원 있는데 어디에 투자하면 될까?"
INTENT: query
MARKET: KR
DATA_SOURCE: hybrid
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": null, "order_by": "rank", "order_direction": "ASC"}}
SUB_QUERIES:
[
  {{"question": "오늘 매수 추천 종목", "market": "KR", "tables": ["daily_recommendation"], "depends_on": null}}
]

### Example 11: Vague good stock question (no buy/invest keyword)
Question: "요즘 괜찮은 종목 있어?"
INTENT: query
MARKET: KR
DATA_SOURCE: hybrid
STOCK_SCOPE: broad
IS_FOLLOW_UP: false
REWRITTEN_QUERY: NONE
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": null, "order_by": "rank", "order_direction": "ASC"}}
SUB_QUERIES:
[
  {{"question": "오늘 매수 추천 종목", "market": "KR", "tables": ["daily_recommendation"], "depends_on": null}}
]

{conversation_context}

User Question: {question}

Respond in this EXACT format (no extra text before or after):
INTENT: <category>
MARKET: <KR|US|BOTH>
DATA_SOURCE: <db_only|hybrid|external_only>
STOCK_SCOPE: <specific|broad>
IS_FOLLOW_UP: <true|false>
REWRITTEN_QUERY: <rewritten self-contained query if IS_FOLLOW_UP=true, otherwise NONE>
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": null, "order_by": null, "order_direction": null}}
SUB_QUERIES:
[
  {{"question": "sub-question in Korean", "market": "KR", "tables": ["table1", "table2"], "depends_on": null}},
  {{"question": "sub-question in Korean", "market": "US", "tables": ["table3"], "depends_on": null}}
]"""


def _build_conversation_context(messages) -> str:
    """Build conversation context string from message history."""
    if not messages:
        return ""

    context_lines = []
    recent_messages = messages[-6:]
    for msg in recent_messages:
        if isinstance(msg, HumanMessage):
            context_lines.append(f"User: {msg.content}")
        else:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            if len(content) > 100:
                content = content[:100] + "..."
            context_lines.append(f"Assistant: {content}")

    if context_lines:
        return "Conversation History:\n" + "\n".join(context_lines)
    return ""


async def _resolve_stocks(
    message: str,
    market_hint: Optional[str] = None,
    accepted_methods: set = None,
) -> Dict[str, Any]:
    """Resolve stock names from message using StockResolver (DB-based, not LLM)."""
    from .entity_extractor import extract_stock_candidates

    result = {"stock_names": [], "stock_codes": [], "stock_info": []}
    resolver = StockResolver.get_instance()

    market = None
    if market_hint == "KR":
        market = Market.KR
    elif market_hint == "US":
        market = Market.US

    candidates = extract_stock_candidates(message)
    if not candidates:
        return result

    methods = accepted_methods or ACCEPTED_MATCH_METHODS

    resolved_symbols = set()
    for candidate in candidates:
        try:
            match_result = await resolver.resolve(candidate, market)
            if (match_result
                    and match_result.method in methods
                    and match_result.stock.symbol not in resolved_symbols):
                resolved_symbols.add(match_result.stock.symbol)
                result["stock_names"].append(match_result.stock.stock_name)
                result["stock_codes"].append(match_result.stock.symbol)
                result["stock_info"].append({
                    "symbol": match_result.stock.symbol,
                    "name": match_result.stock.stock_name,
                    "name_kr": match_result.stock.stock_name_kr,
                    "name_eng": match_result.stock.stock_name_eng,
                    "market": match_result.stock.market.value,
                    "match_method": match_result.method,
                    "confidence": match_result.confidence,
                    "matched_term": match_result.matched_term,
                })
        except Exception as e:
            logger.warning(f"[QueryDecomposer] Failed to resolve '{candidate}': {e}")

    return result


async def _resolve_stocks_from_ai_response(
    ai_content: str,
    market_hint: Optional[str] = None
) -> Dict[str, Any]:
    """Resolve stocks from AI response text using exact match only."""
    from .entity_extractor import extract_stock_candidates

    result = {"stock_names": [], "stock_codes": [], "stock_info": []}
    resolver = StockResolver.get_instance()

    market = None
    if market_hint == "KR":
        market = Market.KR
    elif market_hint == "US":
        market = Market.US

    candidates = extract_stock_candidates(ai_content)
    resolved_symbols = set()

    for candidate in candidates:
        try:
            match_result = await resolver.resolve(candidate, market)
            if (match_result
                    and match_result.method in AI_RESPONSE_MATCH_METHODS
                    and match_result.stock.symbol not in resolved_symbols):
                resolved_symbols.add(match_result.stock.symbol)
                result["stock_names"].append(match_result.stock.stock_name)
                result["stock_codes"].append(match_result.stock.symbol)
                result["stock_info"].append({
                    "symbol": match_result.stock.symbol,
                    "name": match_result.stock.stock_name,
                    "name_kr": match_result.stock.stock_name_kr,
                    "name_eng": match_result.stock.stock_name_eng,
                    "market": match_result.stock.market.value,
                    "match_method": match_result.method,
                    "confidence": match_result.confidence,
                    "matched_term": match_result.matched_term,
                })
        except Exception:
            pass

    return result


def _detect_data_source(message: str, intent: str, llm_data_source: str) -> str:
    """Detect data source with keyword-based override."""
    message_lower = message.lower()

    # Trust LLM classification if it explicitly set external_only
    if llm_data_source == "external_only":
        return "external_only"

    # Hybrid keyword detection
    if any(kw in message_lower for kw in HYBRID_KEYWORDS):
        return "hybrid"

    # External-only detection (only if no DB-related content)
    if any(kw in message_lower for kw in EXTERNAL_ONLY_KEYWORDS):
        if llm_data_source == "external_only":
            return "external_only"
        return "hybrid"  # Usually need both

    return llm_data_source


def _detect_required_apis(message: str, data_source: str) -> List[str]:
    """Detect required external APIs based on message and data source."""
    if data_source == "db_only":
        return []

    required = []
    message_lower = message.lower()

    news_keywords = ["뉴스", "news", "기사", "소식", "보도", "언론"]
    if any(kw in message_lower for kw in news_keywords):
        required.extend(["naver", "serper"])

    analysis_keywords = [
        "리스크", "위험", "요인", "risk", "전망", "리포트",
        "분석", "평가", "의견", "반응", "여론"
    ]
    if any(kw in message_lower for kw in analysis_keywords):
        if "naver" not in required:
            required.append("naver")
        if "serper" not in required:
            required.append("serper")

    disclosure_keywords = ["공시", "disclosure", "발표", "보고서"]
    if any(kw in message_lower for kw in disclosure_keywords):
        required.append("dart")

    if not required and data_source in ["external_only", "hybrid"]:
        required = ["naver", "serper"]

    return required


def _parse_sub_queries(text: str) -> List[Dict[str, Any]]:
    """Parse SUB_QUERIES JSON array from LLM response."""
    # Find the SUB_QUERIES section
    sq_match = re.search(r'SUB_QUERIES:\s*\n?\s*(\[[\s\S]*\])', text)
    if not sq_match:
        return []

    try:
        raw = sq_match.group(1).strip()
        sub_queries = json_module.loads(raw)

        # Validate structure
        validated = []
        for i, sq in enumerate(sub_queries):
            if i >= 7:  # Max 7 sub-queries
                break
            if not isinstance(sq, dict):
                continue
            validated.append({
                "question": sq.get("question", ""),
                "market": sq.get("market", "KR"),
                "tables": sq.get("tables", []),
                "depends_on": sq.get("depends_on"),
            })
        return validated

    except (json_module.JSONDecodeError, Exception) as e:
        logger.warning(f"[QueryDecomposer] Failed to parse SUB_QUERIES JSON: {e}")
        return []


# All valid table names for validation
ALL_VALID_TABLES = {
    # KR tables
    "kr_intraday", "kr_intraday_total", "kr_intraday_detail",
    "kr_indicators", "kr_stock_grade",
    "kr_individual_investor_daily_trading", "kr_investor_daily_trading",
    "kr_program_daily_trading",
    "kr_stock_basic", "kr_stock_detail",
    "kr_blocktrades", "kr_foreign_ownership",
    "kr_financial_position", "kr_dividends", "kr_largest_shareholder",
    "kr_stockacquisitiondisposal", "kr_executive",
    "kr_research_reports",
    "kr_benchmark_index", "mv_sector_daily_performance",
    # US tables
    "us_intraday", "us_daily", "us_daily_etf", "us_weekly", "us_monthly",
    "us_indicators", "us_stock_basic", "us_stock_grade",
    "us_option", "us_option_daily_summary", "us_ipo_calendar",
    "us_income_statement", "us_balance_sheet", "us_cash_flow",
    "us_earnings_estimates", "us_earnings_calendar",
    "us_dividends", "us_splits", "us_news", "us_insider_transactions",
    "us_fed_funds_rate", "us_treasury_yield", "us_cpi",
    "us_unemployment_rate", "us_gdp", "us_pmi",
    "us_market_regime", "us_vix", "us_move_index", "us_dollar_index",
    "us_credit_spread", "us_fed_rrp",
    "us_sector_benchmarks", "mv_us_sector_daily_performance",
    # Common tables
    "market_index", "bok_economic_indicators", "exchange_rate",
    "daily_recommendation",
}


def _validate_sub_query_tables(sub_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove invalid table names from sub-queries."""
    for sq in sub_queries:
        valid_tables = [t for t in sq.get("tables", []) if t in ALL_VALID_TABLES]
        if not valid_tables:
            # Fallback: assign default tables based on market
            if sq.get("market") == "US":
                valid_tables = ["us_daily", "us_stock_basic"]
            else:
                valid_tables = ["kr_intraday_total"]
            logger.warning(
                f"[QueryDecomposer] Sub-query '{sq['question'][:50]}' had no valid tables, "
                f"assigned fallback: {valid_tables}"
            )
        sq["tables"] = valid_tables
    return sub_queries


def _ensure_indicator_coverage(message: str, sub_queries: List[Dict]) -> List[Dict]:
    """Ensure mentioned macro indicators have corresponding sub-queries."""
    INDICATOR_TABLE_MAP = {
        "vix": {"table": "us_vix", "market": "US", "question": "현재 VIX 지수"},
        "cpi": {"table": "us_cpi", "market": "US", "question": "최근 미국 CPI 추이"},
        "기준금리": {"table": "bok_economic_indicators", "market": "KR", "question": "현재 한국 기준금리"},
        "연방금리": {"table": "us_fed_funds_rate", "market": "US", "question": "현재 미국 연방금리"},
        "달러인덱스": {"table": "us_dollar_index", "market": "US", "question": "현재 달러 인덱스"},
        "신용스프레드": {"table": "us_credit_spread", "market": "US", "question": "현재 미국 신용 스프레드"},
    }

    msg_lower = message.lower()
    all_tables = set()
    for sq in sub_queries:
        all_tables.update(sq.get("tables", []))

    added = 0
    for keyword, info in INDICATOR_TABLE_MAP.items():
        if keyword in msg_lower and info["table"] not in all_tables:
            sub_queries.append({
                "question": info["question"],
                "market": info["market"],
                "tables": [info["table"]],
                "depends_on": None,
            })
            added += 1
            logger.info(f"[QueryDecomposer] Added missing indicator: {info['table']}")

    return sub_queries


async def query_decomposer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decompose user query into sub-queries with table assignments.

    Replaces: unified_classifier + entity_extractor + data_source_router + SchemaRAG
    in a single LLM call.

    Args:
        state: Current graph state with 'message' field

    Returns:
        Updated state with intent, market, entities, data_source, sub_queries
    """
    logger.info("[AlphaAI:QueryDecomposer] Processing...")

    message = state.get("message", "")
    provider = state.get("provider")
    model = state.get("model_name")
    messages = state.get("messages", [])

    # Build conversation context
    conversation_context = _build_conversation_context(messages)

    # === Single LLM Call ===
    intent = "query"
    market = "KR"
    stock_scope = "specific"
    data_source = "db_only"
    llm_entities = {}
    sub_queries = []
    expanded_message = None

    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        prompt = DECOMPOSITION_PROMPT.format(
            question=message,
            conversation_context=conversation_context,
        )

        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Parse structured response
        is_follow_up = False
        for line in response_text.strip().split('\n'):
            line = line.strip()
            if line.startswith("INTENT:"):
                intent = line.replace("INTENT:", "").strip().lower()
            elif line.startswith("MARKET:"):
                market = line.replace("MARKET:", "").strip().upper()
            elif line.startswith("STOCK_SCOPE:"):
                stock_scope = line.replace("STOCK_SCOPE:", "").strip().lower()
            elif line.startswith("DATA_SOURCE:"):
                data_source = line.replace("DATA_SOURCE:", "").strip().lower()
            elif line.startswith("IS_FOLLOW_UP:"):
                is_follow_up = line.replace("IS_FOLLOW_UP:", "").strip().lower() == "true"
            elif line.startswith("REWRITTEN_QUERY:"):
                rewritten = line.replace("REWRITTEN_QUERY:", "").strip()
                if rewritten and rewritten.upper() != "NONE" and is_follow_up and len(rewritten) > len(message):
                    expanded_message = rewritten
                    logger.info(
                        f"[QueryDecomposer] Query rewritten: '{message}' -> '{expanded_message}'"
                    )

        # Parse ENTITIES JSON block
        json_match = re.search(r'ENTITIES:\s*\n?\s*(\{[\s\S]*?\})\s*\n\s*SUB_QUERIES:', response_text)
        if not json_match:
            json_match = re.search(r'ENTITIES:\s*\n?\s*(\{[\s\S]*?\})', response_text)
        if json_match:
            try:
                llm_entities = json_module.loads(json_match.group(1))
            except json_module.JSONDecodeError:
                logger.warning("[QueryDecomposer] Failed to parse entities JSON from LLM")

        # Parse SUB_QUERIES
        sub_queries = _parse_sub_queries(response_text)

        # Validate parsed values
        valid_intents = [
            "chat", "explain", "query", "ranking", "filter",
            "technical", "investor", "quant", "market", "analysis"
        ]
        if intent not in valid_intents:
            intent = "query"
        if market not in ["KR", "US", "BOTH"]:
            market = "KR"
        if stock_scope not in ["specific", "broad"]:
            stock_scope = "specific"
        if data_source not in ["db_only", "hybrid", "external_only"]:
            data_source = "db_only"

    except Exception as e:
        logger.error(f"[QueryDecomposer] LLM call failed, using rule-based fallback: {e}")
        from .intent_classifier import classify_with_rules
        rule_result = classify_with_rules(message)
        intent = rule_result["intent"]
        market = rule_result["market"]

    # === Validate and fix sub-queries ===
    if sub_queries:
        sub_queries = _validate_sub_query_tables(sub_queries)
        sub_queries = _ensure_indicator_coverage(message, sub_queries)
    else:
        # Fallback: single sub-query with full market schema
        if intent not in ["chat", "explain"]:
            if market == "US":
                fallback_tables = ["us_daily", "us_stock_basic"]
            elif market == "BOTH":
                fallback_tables = ["kr_intraday_total", "us_daily"]
            else:
                fallback_tables = ["kr_intraday_total"]

            sub_queries = [{
                "question": expanded_message or message,
                "market": market if market != "BOTH" else "KR",
                "tables": fallback_tables,
                "depends_on": None,
            }]
            logger.warning("[QueryDecomposer] No sub-queries parsed, using single fallback")

    # === BOTH market resolution ===
    # In decomposition architecture, each sub-query has its own market (KR/US).
    # Keep BOTH when both markets have sub-queries (legitimate cross-market).
    # Only resolve to single market when all sub-queries target one market.
    if market == "BOTH" and sub_queries:
        kr_count = sum(1 for sq in sub_queries if sq.get("market") == "KR")
        us_count = sum(1 for sq in sub_queries if sq.get("market") == "US")
        if kr_count > 0 and us_count > 0:
            pass  # Keep BOTH - legitimate cross-market query
        elif kr_count > 0:
            market = "KR"
        elif us_count > 0:
            market = "US"
        logger.info(f"[QueryDecomposer] BOTH market resolved to {market} (KR={kr_count}, US={us_count})")

    # === Data source override with keyword detection ===
    data_source = _detect_data_source(message, intent, data_source)

    # === Build entities dict ===
    entities = {
        "stock_names": llm_entities.get("stock_names", []),
        "stock_codes": llm_entities.get("stock_codes", []),
        "stock_info": [],
        "indicators": llm_entities.get("indicators", []),
        "conditions": llm_entities.get("conditions", {}),
        "time_range": llm_entities.get("time_range"),
        "limit": llm_entities.get("limit"),
        "order_by": llm_entities.get("order_by"),
        "order_direction": llm_entities.get("order_direction"),
    }

    # === Rule-based condition extraction (supplement LLM results) ===
    try:
        from .entity_extractor import get_self_query
        self_query = get_self_query()
        rule_filters = self_query._extract_filters_rule_based(message)
        for f in rule_filters:
            if f.column not in entities["conditions"]:
                entities["conditions"][f.column] = {
                    "op": f.operator.value,
                    "value": f.value,
                }
    except Exception as e:
        logger.debug(f"[QueryDecomposer] Rule-based filter extraction failed: {e}")

    # === Stock Resolution using StockResolver (DB-based, not LLM) ===
    try:
        if stock_scope == "broad":
            resolve_methods = {"exact", "alias"}
        else:
            resolve_methods = ACCEPTED_MATCH_METHODS
        stock_result = await _resolve_stocks(expanded_message or message, market, accepted_methods=resolve_methods)
        if stock_result["stock_codes"]:
            entities["stock_names"] = stock_result["stock_names"]
            entities["stock_codes"] = stock_result["stock_codes"]
            entities["stock_info"] = stock_result["stock_info"]
            logger.info(
                f"[QueryDecomposer] StockResolver found "
                f"{len(stock_result['stock_codes'])} stocks"
            )
        else:
            entities["stock_info"] = []
    except Exception as e:
        logger.warning(f"[QueryDecomposer] StockResolver failed: {e}")
        entities["stock_info"] = []

    # === Fallback: resolve stock from conversation history ===
    if not entities.get("stock_codes"):
        if stock_scope == "broad":
            logger.info("[QueryDecomposer] Broad scope query - skipping stock fallback")
        elif not messages:
            entities["stock_fallback_guide"] = True
        else:
            from .entity_extractor import _group_messages_into_turns
            turns = _group_messages_into_turns(messages)
            found = False

            for turn in reversed(turns[-3:]):
                user_content, ai_content = turn

                if user_content:
                    try:
                        history_stock = await _resolve_stocks(user_content, market)
                        if history_stock["stock_codes"]:
                            entities["stock_names"] = history_stock["stock_names"]
                            entities["stock_codes"] = history_stock["stock_codes"]
                            entities["stock_info"] = history_stock["stock_info"]
                            logger.info(
                                f"[QueryDecomposer] Fallback from user turn: "
                                f"{history_stock['stock_names']}"
                            )
                            found = True
                            break
                    except Exception:
                        pass

                if ai_content:
                    try:
                        ai_stock = await _resolve_stocks_from_ai_response(
                            ai_content, market
                        )
                        if ai_stock["stock_codes"]:
                            entities["stock_names"] = ai_stock["stock_names"]
                            entities["stock_codes"] = ai_stock["stock_codes"]
                            entities["stock_info"] = ai_stock["stock_info"]
                            logger.info(
                                f"[QueryDecomposer] Fallback from AI turn (exact only): "
                                f"{ai_stock['stock_names']}"
                            )
                            found = True
                            break
                    except Exception:
                        pass

            if not found:
                entities["stock_fallback_guide"] = True

    # === Query expansion for keywords (rule-based, not LLM) ===
    try:
        from .entity_extractor import get_query_expander
        query_expander = get_query_expander()
        expansion = await query_expander.expand(
            message, use_synonyms=True, use_rewrite=False
        )
        entities["keywords"] = expansion.get("keywords", [])
        entities["expanded_queries"] = expansion.get("expanded", [message])
    except Exception as e:
        logger.debug(f"[QueryDecomposer] Query expansion failed: {e}")
        entities["keywords"] = []
        entities["expanded_queries"] = [message]

    # === Detect required APIs and search scope ===
    required_apis = _detect_required_apis(message, data_source)
    search_scope = "local_only"
    if data_source in ["external_only", "hybrid"]:
        message_lower = message.lower()
        cross_keywords = ["글로벌", "global", "해외", "overseas"]
        if any(kw in message_lower for kw in cross_keywords):
            search_scope = "cross_market"
        elif market == "US":
            search_scope = "global_only"

    # Disclaimer check
    message_lower = message.lower()
    requires_disclaimer = any(
        kw in message_lower for kw in ["추천", "매수", "매도", "투자", "전략", "포지션"]
    )

    logger.info(
        f"[AlphaAI:QueryDecomposer] Intent: {intent}, Market: {market}, "
        f"DataSource: {data_source}, SubQueries: {len(sub_queries)}, "
        f"Stocks: {len(entities.get('stock_names', []))}"
        f"{f', Expanded: {expanded_message}' if expanded_message else ''}"
    )

    return {
        **state,
        "intent": intent,
        "market": market,
        "stock_scope": stock_scope,
        "entities": entities,
        "data_source": data_source,
        "required_apis": required_apis,
        "search_scope": search_scope,
        "requires_disclaimer": requires_disclaimer,
        "sub_queries": sub_queries,
        **({"expanded_message": expanded_message} if expanded_message else {}),
        "processing_steps": state.get("processing_steps", []) + ["query_decomposer"],
    }
