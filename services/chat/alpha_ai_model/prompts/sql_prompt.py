# services/chat/alpha_ai_model/prompts/sql_prompt.py
"""
SQL Generation Prompt

Defines the prompt template for SQL generation from natural language.
Includes detailed table schemas for accurate SQL generation.
"""
from typing import List, Dict, Optional


# =============================================================================
# TABLE SCHEMAS - KOREAN STOCKS (kr_*)
# =============================================================================

KR_INTRADAY_SCHEMA = """
Table: kr_intraday
Description: Korean stock real-time snapshot data (NO date column - current data only)
Primary Key: symbol
Columns:
- symbol (VARCHAR): Stock code (e.g., '005930' for Samsung)
- stock_name (VARCHAR): Stock name in Korean
- exchange (VARCHAR): Exchange (KOSPI, KOSDAQ)
- close (NUMERIC): Current/closing price (KRW)
- change_amount (NUMERIC): Price change amount (KRW)
- change_rate (NUMERIC): Price change rate (%)
- open (NUMERIC): Opening price
- high (NUMERIC): Day high price
- low (NUMERIC): Day low price
- volume (BIGINT): Trading volume (shares)
- trading_value (BIGINT): Trading value (KRW)
- market_cap (NUMERIC): Market capitalization (KRW)
- listed_shares (BIGINT): Listed shares
- avg_trading_value_5d (BIGINT): 5-day average trading value
- avg_trading_value_20d (BIGINT): 20-day average trading value
- avg_trading_value_60d (BIGINT): 60-day average trading value
- avg_trading_value_200d (BIGINT): 200-day average trading value
- avg_volume_5d (BIGINT): 5-day average volume
- avg_volume_20d (BIGINT): 20-day average volume
- avg_volume_60d (BIGINT): 60-day average volume
- avg_volume_200d (BIGINT): 200-day average volume
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: Real-time snapshot only. Use kr_intraday_total for historical queries with date.
IMPORTANT: This table has NO date column. For date-based queries, use kr_intraday_total instead.
"""

KR_INTRADAY_TOTAL_SCHEMA = """
Table: kr_intraday_total
Description: Korean stock historical daily quote data (has date column)
Primary Key: (symbol, date)
Columns:
- symbol (VARCHAR): Stock code
- stock_name (VARCHAR): Stock name in Korean
- exchange (VARCHAR): Exchange (KOSPI, KOSDAQ)
- close (NUMERIC): Closing price (KRW)
- change_amount (NUMERIC): Price change amount (KRW)
- change_rate (NUMERIC): Price change rate (%)
- open (NUMERIC): Opening price
- high (NUMERIC): Day high price
- low (NUMERIC): Day low price
- volume (BIGINT): Trading volume
- trading_value (BIGINT): Trading value (KRW)
- market_cap (NUMERIC): Market capitalization
- listed_shares (BIGINT): Listed shares
- eps (NUMERIC): Earnings per share
- per (NUMERIC): Price to Earnings Ratio
- roe (NUMERIC): Return on Equity
- bps (NUMERIC): Book value per share
- pbr (NUMERIC): Price to Book Ratio
- dps (NUMERIC): Dividend per share
- dividend_yield (NUMERIC): Dividend yield (%)
- date (DATE): Trading date
- avg_trading_value_5d (BIGINT): 5-day average trading value
- avg_trading_value_20d (BIGINT): 20-day average trading value
- avg_trading_value_60d (BIGINT): 60-day average trading value
- avg_trading_value_200d (BIGINT): 200-day average trading value
- avg_volume_5d (BIGINT): 5-day average volume
- avg_volume_20d (BIGINT): 20-day average volume
- avg_volume_60d (BIGINT): 60-day average volume
- avg_volume_200d (BIGINT): 200-day average volume
Usage: Historical data queries. JOIN with kr_indicators ON symbol AND date.
"""

KR_INDICATORS_SCHEMA = """
Table: kr_indicators
Description: Korean stock technical indicators
Primary Key: (symbol, date)
Columns:
- symbol (VARCHAR): Stock code
- stock_name (VARCHAR): Stock name
- date (DATE): Indicator date
- rsi (NUMERIC): RSI (0-100, <30 oversold, >70 overbought)
- macd (NUMERIC): MACD line value
- macd_signal (NUMERIC): MACD signal line
- macd_hist (NUMERIC): MACD histogram (macd - signal)
- real_upper_band (NUMERIC): Bollinger Band upper
- real_middle_band (NUMERIC): Bollinger Band middle (SMA)
- real_lower_band (NUMERIC): Bollinger Band lower
- vwap (NUMERIC): Volume Weighted Average Price
- eod_vwap (NUMERIC): End of day VWAP
- avg_vwap (NUMERIC): Average VWAP
- price_vs_vwap (NUMERIC): Price vs VWAP ratio
- atr (NUMERIC): Average True Range
- slowk (NUMERIC): Stochastic Slow %K
- slowd (NUMERIC): Stochastic Slow %D
- mfi (NUMERIC): Money Flow Index
- roc (NUMERIC): Rate of Change
- sma (NUMERIC): Simple Moving Average
- ema (NUMERIC): Exponential Moving Average
- adx (NUMERIC): Average Directional Index
- wma (NUMERIC): Weighted Moving Average
- aroon (NUMERIC): Aroon indicator
- cci (NUMERIC): Commodity Channel Index
- obv (NUMERIC): On Balance Volume
Usage: JOIN with kr_intraday_total ON symbol AND date for technical analysis
"""

KR_STOCK_GRADE_SCHEMA = """
Table: kr_stock_grade
Description: Korean stock quant analysis model results
Primary Key: (symbol, date)
Columns:
- stock_name (VARCHAR): Stock name
- symbol (VARCHAR): Stock code
- date (DATE): Analysis date (based on kr_intraday_total latest data)
- final_grade (VARCHAR): Investment grade (강력 매수, 매수, 매수 고려, 중립, 매도 고려, 매도, 강력 매도)
- final_score (NUMERIC): Final score (0-100): base_factor_score*0.36 + sector_rotation_score*0.25 + factor_combination_bonus*0.39
- value_score (NUMERIC): Value factor weighted score (0-100)
- quality_score (NUMERIC): Quality factor weighted score (0-100)
- momentum_score (NUMERIC): Momentum factor weighted score (0-100)
- growth_score (NUMERIC): Growth factor weighted score (0-100)
- confidence_score (NUMERIC): Confidence score (%): data completeness(70%) + 4 factor existence(30%)
- var_95 (NUMERIC): Daily VaR 95% (negative, %): 5th percentile of 90-day daily returns
- cvar_95 (NUMERIC): Daily CVaR 95% (negative, %): mean of returns below VaR 95%
- inst_net_30d (BIGINT): Institution 30-day net volume
- foreign_net_30d (BIGINT): Foreign 30-day net volume
- value_momentum (NUMERIC): Value factor momentum: value_score - 50
- quality_momentum (NUMERIC): Quality factor momentum: quality_score - 50
- momentum_momentum (NUMERIC): Momentum factor momentum: momentum_score - 50
- growth_momentum (NUMERIC): Growth factor momentum: growth_score - 50
- industry_rank (INTEGER): Industry rank by market cap
- industry_percentile (NUMERIC): Industry percentile (%)
- beta (NUMERIC): Beta coefficient estimate
- volatility_annual (NUMERIC): Annualized volatility (%)
- max_drawdown_1y (NUMERIC): 1-year max drawdown (negative, %)
- risk_profile_text (TEXT): Risk profile interpretation
- risk_recommendation (TEXT): Investor suitability recommendation
- time_series_text (TEXT): Time series trend interpretation
- signal_overall (TEXT): Overall signal evaluation
- market_state (VARCHAR): Market state classification (19 dimensions)
- rs_value (NUMERIC): Relative Strength value (%): stock 20d return - market avg 20d return
- rs_rank (TEXT): Relative Strength grade (Very Strong, Strong, Neutral, Weak, Very Weak)
- factor_combination_bonus (INTEGER): Factor combination bonus (0-100 normalized)
- sector_rotation_score (INTEGER): Sector rotation score (0-100)
- sector_momentum (NUMERIC): Sector momentum (%): sector avg 30d return
- sector_rank (INTEGER): Sector rank by return
- sector_percentile (NUMERIC): Sector percentile (top X%)
- value_v2_detail (JSONB): Value factor strategy details JSON
- quality_v2_detail (JSONB): Quality factor strategy details JSON
- momentum_v2_detail (JSONB): Momentum factor strategy details JSON
- growth_v2_detail (JSONB): Growth factor strategy details JSON
- entry_timing_score (NUMERIC): Entry timing score (0-100)
- score_trend_2w (NUMERIC): 2-week final_score change
- price_position_52w (NUMERIC): 52-week high/low position (0-100%)
- stop_loss_pct (NUMERIC): Stop loss % (negative): -2 * ATR%
- take_profit_pct (NUMERIC): Take profit % (positive): +3 * ATR%
- risk_reward_ratio (NUMERIC): Risk/reward ratio (default 1.5)
- position_size_pct (NUMERIC): Recommended portfolio weight (%)
- atr_pct (NUMERIC): ATR% (14-day)
- scenario_bullish_prob (INTEGER): Bullish scenario probability (%)
- scenario_sideways_prob (INTEGER): Sideways scenario probability (%)
- scenario_bearish_prob (INTEGER): Bearish scenario probability (%)
- scenario_bullish_return (VARCHAR): Bullish expected return range
- scenario_sideways_return (VARCHAR): Sideways expected return range
- scenario_bearish_return (VARCHAR): Bearish expected return range
- scenario_sample_count (INTEGER): Scenario analysis sample count
- buy_triggers (JSONB): Buy trigger conditions JSON array
- sell_triggers (JSONB): Sell trigger conditions JSON array
- hold_triggers (JSONB): Hold trigger conditions JSON array
- sharpe_ratio (NUMERIC): Sharpe ratio
- sortino_ratio (NUMERIC): Sortino ratio
- calmar_ratio (NUMERIC): Calmar ratio
- strategy (JSON): Multi AI agent investment strategy analysis
- hurst_exponent (FLOAT): Hurst exponent (0-1): <0.5 mean reversion, =0.5 random walk, >0.5 trend persistence
- var_95_ewma (FLOAT): EWMA VaR 95% (%): exponentially weighted moving average volatility based VaR
- var_95_5d (FLOAT): 5-day VaR 95% (negative, %)
- var_95_20d (FLOAT): 20-day VaR 95% (negative, %)
- var_95_60d (FLOAT): 60-day VaR 95% (negative, %)
- var_99 (FLOAT): Daily VaR 99% (negative, %)
- var_99_60d (FLOAT): 60-day VaR 99% (negative, %)
- inv_vol_weight (FLOAT): Inverse volatility weight
- downside_vol (FLOAT): Downside volatility (%)
- vol_percentile (FLOAT): Volatility percentile (%)
- atr_20d (FLOAT): ATR 20-day (KRW)
- atr_pct_20d (FLOAT): ATR% 20-day (%)
- cvar_99 (FLOAT): CVaR 99% (negative, %)
- corr_kospi (FLOAT): KOSPI correlation (-1 to 1)
- corr_sector_avg (FLOAT): Sector average correlation (-1 to 1)
- tail_beta (FLOAT): Tail Beta: beta during market decline (<-5%)
- drawdown_duration_avg (FLOAT): Average drawdown duration (trading days)
- conviction_score (NUMERIC): Conviction score (0-100): based on consistency of 4 factor scores - lower std dev = higher score
- outlier_risk_score (NUMERIC): ORS (Outlier Risk Score, 0-100): Penny Stock(<1000KRW, 25pts) + Volume(low liquidity, 25pts) + Volatility(>80%, 25pts) + Market Cap(small cap, 25pts)
- risk_flag (VARCHAR): Risk grade based on ORS: EXTREME_RISK(>=80), HIGH_RISK(>=60), MODERATE_RISK(>=40), NORMAL(<40)
- alt_symbol (VARCHAR): Alternative stock code recommendation
- alt_stock_name (VARCHAR): Alternative stock name
- alt_final_grade (VARCHAR): Alternative stock investment grade
- alt_final_score (NUMERIC): Alternative stock final score
- alt_match_type (VARCHAR): Alternative match type (same_industry, similar_score, higher_quality, lower_risk)
- alt_reasons (JSONB): Alternative stock recommendation reasons JSON array
- value_rank (VARCHAR): Value factor rank ('X위' or '공동 X위' format)
- value_percentile (NUMERIC): Value factor percentile (0-100%, 0%=top)
- quality_rank (VARCHAR): Quality factor rank
- quality_percentile (NUMERIC): Quality factor percentile (0-100%)
- momentum_rank (VARCHAR): Momentum factor rank
- momentum_percentile (NUMERIC): Momentum factor percentile (0-100%)
- growth_rank (VARCHAR): Growth factor rank
- growth_percentile (NUMERIC): Growth factor percentile (0-100%)
- created_at (TIMESTAMP): Record creation time
Usage: JOIN with kr_intraday_total ON symbol for quant screening. Use final_grade for investment rating filtering.
"""

KR_INDIVIDUAL_INVESTOR_DAILY_TRADING_SCHEMA = """
Table: kr_individual_investor_daily_trading
Description: Per-stock investor type trading data (foreign, institution, retail)
Primary Key: (symbol, date)
Columns:
- date (DATE): Trading date
- symbol (VARCHAR): Stock code
- inst_buy_volume (BIGINT): Institution buy volume
- inst_sell_volume (BIGINT): Institution sell volume
- inst_net_volume (BIGINT): Institution net volume
- inst_buy_value (BIGINT): Institution buy value (KRW)
- inst_sell_value (BIGINT): Institution sell value (KRW)
- inst_net_value (BIGINT): Institution net value (KRW)
- inst_buy_ratio (DECIMAL): Institution buy ratio (%)
- retail_buy_volume (BIGINT): Retail/individual buy volume
- retail_sell_volume (BIGINT): Retail sell volume
- retail_net_volume (BIGINT): Retail net volume
- retail_buy_value (BIGINT): Retail buy value (KRW)
- retail_sell_value (BIGINT): Retail sell value (KRW)
- retail_net_value (BIGINT): Retail net value (KRW)
- retail_buy_ratio (DECIMAL): Retail buy ratio (%)
- foreign_buy_volume (BIGINT): Foreign buy volume
- foreign_sell_volume (BIGINT): Foreign sell volume
- foreign_net_volume (BIGINT): Foreign net volume (buy - sell)
- foreign_buy_value (BIGINT): Foreign buy value (KRW)
- foreign_sell_value (BIGINT): Foreign sell value (KRW)
- foreign_net_value (BIGINT): Foreign net value (KRW)
- foreign_buy_ratio (DECIMAL): Foreign buy ratio (%)
- total_buy_volume (BIGINT): Total buy volume
- total_sell_volume (BIGINT): Total sell volume
- total_net_volume (BIGINT): Total net volume
- total_buy_value (BIGINT): Total trading value
- total_sell_value (BIGINT): Total sell value
- total_net_value (BIGINT): Total net value
Usage: JOIN with kr_intraday ON symbol for investor flow analysis
"""

KR_STOCK_BASIC_SCHEMA = """
Table: kr_stock_basic
Description: Stock basic information
Primary Key: symbol
Columns:
- symbol (VARCHAR): Stock code
- stock_name (VARCHAR): Stock name
- standard_symbol (VARCHAR): Standard symbol code
- standard_stock_name (VARCHAR): Standard stock name
- stock_name_eng (VARCHAR): English stock name
- exchange (VARCHAR): Exchange (KOSPI, KOSDAQ)
- listed_date (DATE): IPO/listing date
- securities_type (VARCHAR): Securities type
- department (VARCHAR): Department
- stock_type (VARCHAR): Stock type
- par_value (BIGINT): Par value
- listed_shares (BIGINT): Listed shares
- aliases (TEXT[]): Stock name aliases for fuzzy matching
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: Reference table for stock metadata
"""

KR_INTRADAY_DETAIL_SCHEMA = """
Table: kr_intraday_detail
Description: Korean stock real-time detailed valuation data
Primary Key: symbol
Columns:
- symbol (VARCHAR): Stock code
- stock_name (VARCHAR): Stock name
- close (NUMERIC): Closing price
- change_amount (NUMERIC): Price change amount
- change_rate (NUMERIC): Price change rate (%)
- eps (NUMERIC): Earnings per share
- per (NUMERIC): Price to Earnings Ratio
- bps (NUMERIC): Book value per share
- pbr (NUMERIC): Price to Book Ratio
- dps (NUMERIC): Dividend per share
- dividend_yield (NUMERIC): Dividend yield (%)
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: Real-time valuation metrics snapshot
"""

KR_INVESTOR_DAILY_TRADING_SCHEMA = """
Table: kr_investor_daily_trading
Description: Market-wide investor type trading summary (not per-stock)
Primary Key: (investor_type, date)
Columns:
- investor_type (VARCHAR): Investor category (foreign, institution, retail, etc.)
- sell_volume (BIGINT): Sell volume
- buy_volume (BIGINT): Buy volume
- net_buy_volume (BIGINT): Net buy volume
- sell_value (BIGINT): Sell value (KRW)
- buy_value (BIGINT): Buy value (KRW)
- net_buy_value (BIGINT): Net buy value (KRW)
- date (DATE): Trading date
Usage: Market-wide investor flow analysis. For per-stock data, use kr_individual_investor_daily_trading.
"""

KR_PROGRAM_DAILY_TRADING_SCHEMA = """
Table: kr_program_daily_trading
Description: Program trading daily summary
Primary Key: (category, date)
Columns:
- category (VARCHAR): Trading category
- sell_volume (BIGINT): Sell volume
- buy_volume (BIGINT): Buy volume
- net_buy_volume (BIGINT): Net buy volume
- sell_value (BIGINT): Sell value (KRW)
- buy_value (BIGINT): Buy value (KRW)
- net_buy_value (BIGINT): Net buy value (KRW)
- date (DATE): Trading date
Usage: Program trading flow analysis
"""

KR_BLOCKTRADES_SCHEMA = """
Table: kr_blocktrades
Description: Block trade data (large volume transactions)
Primary Key: (symbol, date)
Columns:
- symbol (VARCHAR): Stock code
- stock_name (VARCHAR): Stock name
- close (NUMERIC): Closing price
- change_amount (NUMERIC): Price change amount
- change_rate (NUMERIC): Price change rate (%)
- volume (BIGINT): Trading volume
- block_volume (BIGINT): Block trade volume
- block_volume_rate (NUMERIC): Block trade volume ratio (%)
- date (DATE): Trading date
Usage: Large transaction analysis, institutional activity detection
"""

KR_FOREIGN_OWNERSHIP_SCHEMA = """
Table: kr_foreign_ownership
Description: Foreign investor ownership data
Primary Key: (symbol, date)
Columns:
- symbol (VARCHAR): Stock code
- stock_name (VARCHAR): Stock name
- close (NUMERIC): Closing price
- change_amount (NUMERIC): Price change amount
- change_rate (NUMERIC): Price change rate (%)
- listed_shares (BIGINT): Listed shares
- foreign_ownership (BIGINT): Foreign ownership shares
- foreign_rate (NUMERIC): Foreign ownership rate (%)
- foreign_limit (BIGINT): Foreign ownership limit
- foreign_rate_limit (NUMERIC): Foreign limit utilization rate (%)
- date (DATE): Trading date
Usage: Foreign investment flow and limit analysis
"""

KR_STOCK_DETAIL_SCHEMA = """
Table: kr_stock_detail
Description: Detailed stock company information
Primary Key: symbol
Columns:
- symbol (VARCHAR): Stock code
- stock_name (VARCHAR): Stock name
- exchange (VARCHAR): Exchange (KOSPI, KOSDAQ)
- department (VARCHAR): Department
- industry_code (VARCHAR): Industry code
- industry (VARCHAR): Industry name
- fiscal_month (INTEGER): Fiscal year end month
- advisor (VARCHAR): Designated advisor
- listed_shares (BIGINT): Listed shares
- par_value (BIGINT): Par value
- capital (BIGINT): Capital
- currency (VARCHAR): Currency code
- ceo_name (VARCHAR): CEO name
- phone (VARCHAR): Company phone
- address (VARCHAR): Company address
- theme (VARCHAR): Investment theme (17 values: Semiconductor, AI_BigData, Battery, Bio_DrugRD, Consumer_Goods, Electronics, Energy, Finance, Healthcare_Device, IT_Software, Materials_Chemical, Others, Pharma_CDMO, Shipbuilding, Telecom_Media, Traditional_Manufacturing, Advanced_Manufacturing). Use for "관련주" broad filtering. Covers broader scope than industry.
- industry (VARCHAR): KSIC industry classification (Korean text, e.g. 반도체 제조업, 의약품 제조업). Use for specific industry filtering.
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: Company fundamental information lookup
"""

KR_FINANCIAL_POSITION_SCHEMA = """
Table: kr_financial_position
Description: Company financial statements data (from DART)
Primary Key: (symbol, rcept_no, account_id)
Columns:
- stock_name (VARCHAR): Stock name
- symbol (VARCHAR): Stock code
- report_code (VARCHAR): Report code
- bsns_year (INTEGER): Business year
- corp_code (VARCHAR): Corporate code
- fs_div (VARCHAR): Financial statement type (OFS: individual, CFS: consolidated)
- sj_div (VARCHAR): Statement division (BS, IS, CF)
- sj_nm (VARCHAR): Statement name
- account_id (VARCHAR): Account ID
- account_nm (VARCHAR): Account name
- account_detail (TEXT): Account detail
- thstrm_nm (VARCHAR): Current term name
- thstrm_amount (BIGINT): Current term amount
- thstrm_add_amount (BIGINT): Current term accumulated amount
- frmtrm_nm (VARCHAR): Prior term name
- frmtrm_amount (BIGINT): Prior term amount
- frmtrm_q_nm (VARCHAR): Prior quarter name
- frmtrm_q_amount (BIGINT): Prior quarter amount
- frmtrm_add_amount (BIGINT): Prior term accumulated amount
- bfefrmtrm_nm (VARCHAR): Before prior term name
- bfefrmtrm_amount (BIGINT): Before prior term amount
- ord (INTEGER): Account sort order
- currency (VARCHAR): Currency unit
- rcept_no (VARCHAR): Receipt number
- fs_nm (VARCHAR): Financial statement name
- thstrm_dt (VARCHAR): Current term date
- frmtrm_dt (VARCHAR): Prior term date
- rcept_dt (DATE): Disclosure date
Usage: Financial analysis, fundamental screening
"""

KR_DIVIDENDS_SCHEMA = """
Table: kr_dividends
Description: Dividend information
Primary Key: (symbol, rcept_no)
Columns:
- symbol (VARCHAR): Stock code
- rcept_no (VARCHAR): Receipt number
- corp_cls (VARCHAR): Corp type (Y: KOSPI, K: KOSDAQ, N: KONEX, E: etc)
- corp_code (VARCHAR): Corporate code
- corp_name (VARCHAR): Company name
- se (VARCHAR): Dividend type (rights offering, warrant exercise, etc.)
- stock_knd (VARCHAR): Stock type (common stock, etc.)
- thstrm (NUMERIC): Current term dividend
- frmtrm (NUMERIC): Prior term dividend
- lwfr (NUMERIC): Before prior term dividend
- stlm_dt (DATE): Settlement date
Usage: Dividend analysis, income investing screening
"""

KR_LARGEST_SHAREHOLDER_SCHEMA = """
Table: kr_largest_shareholder
Description: Largest shareholder information
Primary Key: (symbol, rcept_no, nm)
Columns:
- symbol (VARCHAR): Stock code
- rcept_no (VARCHAR): Receipt number
- corp_cls (VARCHAR): Corp type (Y: KOSPI, K: KOSDAQ, N: KONEX, E: etc)
- corp_code (VARCHAR): Corporate code
- corp_name (VARCHAR): Company name
- nm (VARCHAR): Shareholder name
- relate (VARCHAR): Relationship (self, relative, etc.)
- stock_knd (VARCHAR): Stock type
- bsis_posesn_stock_co (BIGINT): Beginning shares held
- bsis_posesn_stock_qota_rt (NUMERIC): Beginning ownership rate (%)
- trmend_posesn_stock_co (BIGINT): Ending shares held
- trmend_posesn_stock_qota_rt (NUMERIC): Ending ownership rate (%)
- rm (TEXT): Remarks
- stlm_dt (DATE): Settlement date
Usage: Ownership structure analysis
"""

KR_STOCKACQUISITIONDISPOSAL_SCHEMA = """
Table: kr_stockacquisitiondisposal
Description: Treasury stock acquisition and disposal status
Primary Key: (symbol, rcept_no)
Columns:
- symbol (VARCHAR): Stock code
- rcept_no (VARCHAR): Receipt number
- corp_cls (VARCHAR): Corp type (Y: KOSPI, K: KOSDAQ, N: KONEX, E: etc)
- corp_code (VARCHAR): Corporate code
- corp_name (VARCHAR): Company name
- acqs_mth1 (VARCHAR): Acquisition method (major category)
- acqs_mth2 (VARCHAR): Acquisition method (mid category)
- acqs_mth3 (VARCHAR): Acquisition method (minor category)
- stock_knd (VARCHAR): Stock type
- bsis_qy (BIGINT): Beginning quantity
- change_qy_acqs (BIGINT): Acquired quantity
- change_qy_dsps (BIGINT): Disposed quantity
- change_qy_incnr (BIGINT): Retired quantity
- trmend_qy (BIGINT): Ending quantity
- rm (TEXT): Remarks
- stlm_dt (DATE): Settlement date
Usage: Treasury stock and buyback analysis
"""

KR_EXECUTIVE_SCHEMA = """
Table: kr_executive
Description: Executive information (from DART)
Primary Key: (symbol, rcept_no, nm)
Columns:
- symbol (VARCHAR): Stock code
- rcept_no (VARCHAR): Receipt number
- corp_cls (VARCHAR): Corp type (Y: KOSPI, K: KOSDAQ, N: KONEX, E: etc)
- corp_code (VARCHAR): Corporate code
- corp_name (VARCHAR): Company name
- nm (VARCHAR): Executive name
- sexdstn (VARCHAR): Gender
- birth_ym (VARCHAR): Birth year/month
- ofcps (VARCHAR): Position
- rgist_exctv_at (VARCHAR): Registered executive status
- fte_at (VARCHAR): Full-time status
- chrg_job (VARCHAR): Responsibility
- main_career (VARCHAR): Main career
- mxmm_shrholdr_relate (VARCHAR): Relationship with largest shareholder
- hffc_pd (VARCHAR): Tenure period
- tenure_end_on (VARCHAR): Tenure end date
- stlm_dt (DATE): Settlement date
Usage: Corporate governance analysis
"""

KR_RESEARCH_REPORTS_SCHEMA = """
Table: kr_research_reports
Description: Securities firm research reports
Primary Key: report_id
Columns:
- report_id (INTEGER): Report ID (PK)
- stock_name (VARCHAR): Company name
- symbol (VARCHAR): Stock code
- title (TEXT): Report title
- securities_firm (VARCHAR): Securities firm name
- date (DATE): Publication date
- target_price (NUMERIC): Target price
- investment_opinion (VARCHAR): Investment opinion
- summary (TEXT): Report summary
- pdf_url (TEXT): Report PDF URL
- created_at (TIMESTAMP): Record creation time
Usage: Analyst research and target price analysis
"""

KR_BENCHMARK_INDEX_SCHEMA = """
Table: kr_benchmark_index
Description: Benchmark index data (KOSPI sub-indices, volatility, futures, gold)
Primary Key: (index_name, date)
Columns:
- id (SERIAL): ID
- index_name (VARCHAR): Index name
- index_category (VARCHAR): Category (kospi, kosdaq, volatility, futures, gold)
- date (DATE): Trading date
- close (NUMERIC): Closing value
- change_amount (NUMERIC): Change amount
- change_rate (NUMERIC): Change rate (%)
- open (NUMERIC): Opening value
- high (NUMERIC): High value
- low (NUMERIC): Low value
- volume (BIGINT): Trading volume
- trading_value (BIGINT): Trading value
- market_cap (BIGINT): Market capitalization
- created_at (TIMESTAMP): Record creation time
Usage: Benchmark comparison, sector index analysis
"""

MV_SECTOR_DAILY_PERFORMANCE_SCHEMA = """
Table: mv_sector_daily_performance
Description: Sector daily performance materialized view (Korean market)
Primary Key: (date, sector_code)
Columns:
- date (DATE): Trading date
- sector_code (VARCHAR): Sector code
- avg_return_30d (NUMERIC): 30-day average return
- stock_count (INTEGER): Number of stocks in sector
- sector_rank (INTEGER): Sector rank by performance
Usage: Sector rotation analysis, industry momentum screening
"""


# =============================================================================
# TABLE SCHEMAS - US STOCKS (us_*)
# =============================================================================

US_DAILY_SCHEMA = """
Table: us_daily
Description: US stock daily quote data
Primary Key: (symbol, date)
Columns:
- date (DATE): Trading date
- symbol (VARCHAR): Stock ticker (e.g., 'AAPL', 'TSLA')
- open (NUMERIC): Opening price (USD)
- high (NUMERIC): Day high price
- low (NUMERIC): Day low price
- close (NUMERIC): Closing price
- volume (BIGINT): Trading volume
- change_amount (NUMERIC): Daily change amount
- change_rate (NUMERIC): Daily change rate (%)
- per (NUMERIC): Price to Earnings Ratio
- pbr (NUMERIC): Price to Book Ratio
- avg_volume_5d (BIGINT): 5-day average volume
- avg_volume_20d (BIGINT): 20-day average volume
- avg_volume_50d (BIGINT): 50-day average volume
- avg_volume_200d (BIGINT): 200-day average volume
- avg_trading_value_5d (BIGINT): 5-day average trading value
- avg_trading_value_20d (BIGINT): 20-day average trading value
- updated_at (TIMESTAMP): Last update time
Usage: Main table for US stock quotes
"""

US_INDICATORS_SCHEMA = """
Table: us_indicators
Description: US stock technical indicators
Primary Key: (symbol, date)
Columns:
- symbol (VARCHAR): Stock ticker
- stock_name (VARCHAR): Stock name
- date (DATE): Indicator date
- rsi (NUMERIC): RSI (0-100, <30 oversold, >70 overbought)
- macd (NUMERIC): MACD value
- macd_signal (NUMERIC): MACD signal line
- macd_hist (NUMERIC): MACD histogram
- real_upper_band (NUMERIC): Bollinger Band upper
- real_middle_band (NUMERIC): Bollinger Band middle
- real_lower_band (NUMERIC): Bollinger Band lower
- vwap (NUMERIC): Volume Weighted Average Price
- eod_vwap (NUMERIC): End of day VWAP
- avg_vwap (NUMERIC): Average VWAP
- price_vs_vwap (NUMERIC): Price vs VWAP ratio
- atr (NUMERIC): Average True Range
- slowk (NUMERIC): Stochastic Slow %K
- slowd (NUMERIC): Stochastic Slow %D
- mfi (NUMERIC): Money Flow Index
- roc (NUMERIC): Rate of Change
- sma (NUMERIC): Simple Moving Average
- ema (NUMERIC): Exponential Moving Average
- adx (NUMERIC): Average Directional Index
- wma (NUMERIC): Weighted Moving Average
- aroon (NUMERIC): Aroon indicator
- cci (NUMERIC): Commodity Channel Index
- obv (NUMERIC): On Balance Volume
Usage: JOIN with us_daily ON symbol AND date
"""

US_STOCK_BASIC_SCHEMA = """
Table: us_stock_basic
Description: US stock basic information
Primary Key: symbol
Columns:
- symbol (VARCHAR): Stock ticker
- assettype (VARCHAR): Asset type (e.g., Common Stock)
- stock_name (TEXT): Company name
- description (TEXT): Company description
- cik (VARCHAR): CIK number
- exchange (VARCHAR): Exchange (NYSE, NASDAQ, AMEX)
- currency (VARCHAR): Currency code (e.g., USD)
- country (VARCHAR): Country
- sector (VARCHAR): Broad sector (14 values, UPPERCASE: TECHNOLOGY, HEALTHCARE, FINANCIAL SERVICES, INDUSTRIALS, CONSUMER CYCLICAL, COMMUNICATION SERVICES, REAL ESTATE, CONSUMER DEFENSIVE, BASIC MATERIALS, ENERGY, UTILITIES, FINANCIALS, NONE, OTHER). Use for broad filtering.
- industry (VARCHAR): Specific industry (152 values, UPPERCASE). Examples: SEMICONDUCTORS, SEMICONDUCTOR EQUIPMENT & MATERIALS, BIOTECHNOLOGY, SOFTWARE - APPLICATION, SOFTWARE - INFRASTRUCTURE, BANKS - REGIONAL, MEDICAL DEVICES, AEROSPACE & DEFENSE, OIL & GAS E&P, CONSUMER ELECTRONICS, AUTO MANUFACTURERS, INTERNET CONTENT & INFORMATION. Use for specific filtering. IMPORTANT: Use industry (not sector) for specific industries like semiconductor, biotech, software.
- address (TEXT): Company address
- officialSite (TEXT): Official website URL
- fiscalyearend (VARCHAR): Fiscal year end month
- latestquarter (DATE): Latest quarter date
- market_cap (BIGINT): Market capitalization (USD)
- ebitda (BIGINT): EBITDA
- per (NUMERIC): Price to Earnings Ratio
- peg (NUMERIC): PEG ratio
- bookvalue (NUMERIC): Book value per share
- dividendpershare (NUMERIC): Dividend per share
- dividendyield (NUMERIC): Dividend yield
- eps (NUMERIC): Earnings per share
- revenuepersharettm (NUMERIC): Revenue per share TTM
- profitmargin (NUMERIC): Profit margin
- operatingmarginttm (NUMERIC): Operating margin TTM
- returnonassetsttm (NUMERIC): Return on assets TTM
- returnonequityttm (NUMERIC): Return on equity TTM
- revenuettm (BIGINT): Revenue TTM
- grossprofitttm (BIGINT): Gross profit TTM
- dilutedepsttm (NUMERIC): Diluted EPS TTM
- quarterlyearningsgrowthyoy (NUMERIC): Quarterly earnings growth YoY
- quarterlyrevenuegrowthyoy (NUMERIC): Quarterly revenue growth YoY
- analysttargetprice (NUMERIC): Analyst target price
- analystratingstrongbuy (INTEGER): Analyst strong buy ratings
- analystratingbuy (INTEGER): Analyst buy ratings
- analystratinghold (INTEGER): Analyst hold ratings
- analystratingsell (INTEGER): Analyst sell ratings
- analystratingstrongsell (INTEGER): Analyst strong sell ratings
- trailingpe (NUMERIC): Trailing PE ratio
- forwardpe (NUMERIC): Forward PE ratio
- pricetosalesratiottm (NUMERIC): Price to sales ratio TTM
- pricetobookratio (NUMERIC): Price to book ratio
- evtorevenue (NUMERIC): EV to revenue
- evtoebitda (NUMERIC): EV to EBITDA
- beta (NUMERIC): Beta coefficient
- week52high (NUMERIC): 52-week high
- week52low (NUMERIC): 52-week low
- day50movingaverage (NUMERIC): 50-day moving average
- day200movingaverage (NUMERIC): 200-day moving average
- sharesoutstanding (BIGINT): Shares outstanding
- sharesfloat (BIGINT): Shares float
- percentinsiders (NUMERIC): Insider ownership (%)
- percentinstitutions (NUMERIC): Institutional ownership (%)
- dividenddate (DATE): Dividend date
- exdividenddate (DATE): Ex-dividend date
- stock_name_kr (VARCHAR): Korean stock name (e.g., Apple, Tesla in Korean)
- aliases (TEXT[]): Stock name aliases for fuzzy matching
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: Reference table for US stock metadata, fundamental analysis
"""

US_INTRADAY_SCHEMA = """
Table: us_intraday
Description: US stock intraday data
Primary Key: (symbol, date)
Columns:
- date (TIMESTAMP): Date and time
- symbol (VARCHAR): Stock ticker
- open (NUMERIC): Opening price
- high (NUMERIC): High price
- low (NUMERIC): Low price
- close (NUMERIC): Closing price
- volume (BIGINT): Trading volume
- updated_at (TIMESTAMP): Last update time
Usage: Intraday price data for US stocks
"""

US_DAILY_ETF_SCHEMA = """
Table: us_daily_etf
Description: US ETF daily quote data
Primary Key: (symbol, date)
Columns:
- date (DATE): Trading date
- symbol (VARCHAR): ETF ticker
- open (NUMERIC): Opening price
- high (NUMERIC): High price
- low (NUMERIC): Low price
- close (NUMERIC): Closing price
- volume (BIGINT): Trading volume
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: ETF price data analysis
"""

US_WEEKLY_SCHEMA = """
Table: us_weekly
Description: US stock weekly quote data
Primary Key: (symbol, date)
Columns:
- date (DATE): Week end date
- symbol (VARCHAR): Stock ticker
- open (NUMERIC): Opening price
- high (NUMERIC): High price
- low (NUMERIC): Low price
- close (NUMERIC): Closing price
- volume (BIGINT): Trading volume
- updated_at (TIMESTAMP): Last update time
Usage: Weekly price data for longer-term analysis
"""

US_MONTHLY_SCHEMA = """
Table: us_monthly
Description: US stock monthly quote data
Primary Key: (symbol, date)
Columns:
- date (DATE): Month end date
- symbol (VARCHAR): Stock ticker
- open (NUMERIC): Opening price
- high (NUMERIC): High price
- low (NUMERIC): Low price
- close (NUMERIC): Closing price
- volume (BIGINT): Trading volume
- updated_at (TIMESTAMP): Last update time
Usage: Monthly price data for long-term analysis
"""

US_OPTION_SCHEMA = """
Table: us_option
Description: US stock options data
Primary Key: contract_id
Columns:
- contract_id (VARCHAR): Option contract ID
- symbol (VARCHAR): Underlying stock ticker
- expiration (DATE): Expiration date
- strike (NUMERIC): Strike price
- type (VARCHAR): Option type (call/put)
- last (NUMERIC): Last traded price
- mark (NUMERIC): Mark price
- bid (NUMERIC): Bid price
- bid_size (INTEGER): Bid size
- ask (NUMERIC): Ask price
- ask_size (INTEGER): Ask size
- volume (INTEGER): Trading volume
- open_interest (INTEGER): Open interest
- date (DATE): Data date
- implied_volatility (NUMERIC): Implied volatility
- delta (NUMERIC): Delta
- gamma (NUMERIC): Gamma
- theta (NUMERIC): Theta
- vega (NUMERIC): Vega
- rho (NUMERIC): Rho
Usage: Options chain analysis, volatility trading
"""

US_OPTION_DAILY_SUMMARY_SCHEMA = """
Table: us_option_daily_summary
Description: US options daily summary statistics
Primary Key: (symbol, date)
Columns:
- symbol (VARCHAR): Stock ticker
- date (DATE): Trading date
- total_call_volume (BIGINT): Total call option volume
- total_put_volume (BIGINT): Total put option volume
- avg_implied_volatility (NUMERIC): Average implied volatility
- min_implied_volatility (NUMERIC): Minimum implied volatility
- max_implied_volatility (NUMERIC): Maximum implied volatility
- avg_call_iv (NUMERIC): Average call IV
- avg_put_iv (NUMERIC): Average put IV
- call_option_count (INTEGER): Number of call options
- put_option_count (INTEGER): Number of put options
- net_gex (NUMERIC): Net gamma exposure
- call_gex (NUMERIC): Call gamma exposure
- put_gex (NUMERIC): Put gamma exposure
- gex_ratio (NUMERIC): GEX ratio
- gamma_flip_distance (NUMERIC): Distance to gamma flip level
Usage: Options flow analysis, put/call ratio, gamma exposure
"""

US_IPO_CALENDAR_SCHEMA = """
Table: us_ipo_calendar
Description: US IPO calendar
Primary Key: symbol
Columns:
- symbol (VARCHAR): Stock ticker
- name (VARCHAR): Company name
- ipodate (DATE): IPO date
- priceRangeLow (NUMERIC): IPO price range low
- priceRangeHigh (NUMERIC): IPO price range high
- currency (VARCHAR): Currency
- exchange (VARCHAR): Exchange
- created_at (TIMESTAMP): Record creation time
Usage: IPO tracking and analysis
"""

US_FED_FUNDS_RATE_SCHEMA = """
Table: us_fed_funds_rate
Description: Federal funds rate data
Primary Key: date
Columns:
- name (VARCHAR): Indicator name (e.g., Effective Federal Funds Rate)
- interval (VARCHAR): Data interval (e.g., monthly)
- unit (VARCHAR): Unit (e.g., percent)
- date (DATE): Data date
- value (NUMERIC): Rate value
- created_at (TIMESTAMP): Record creation time
Usage: Federal Reserve policy analysis
"""

US_TREASURY_YIELD_SCHEMA = """
Table: us_treasury_yield
Description: US Treasury yield data
Primary Key: date
Columns:
- name (VARCHAR): Indicator name (e.g., 10-Year Treasury Constant Maturity Rate)
- interval (VARCHAR): Data interval
- unit (VARCHAR): Unit (percent)
- date (DATE): Data date
- value (NUMERIC): Yield value
- created_at (TIMESTAMP): Record creation time
Usage: Yield curve analysis, interest rate monitoring
"""

US_CPI_SCHEMA = """
Table: us_cpi
Description: US Consumer Price Index data
Primary Key: date
Columns:
- name (VARCHAR): Indicator name
- interval (VARCHAR): Data interval (monthly)
- unit (VARCHAR): Unit (percent)
- date (DATE): Data date
- value (NUMERIC): CPI value
- created_at (TIMESTAMP): Record creation time
Usage: Inflation analysis
"""

US_UNEMPLOYMENT_RATE_SCHEMA = """
Table: us_unemployment_rate
Description: US unemployment rate data
Primary Key: date
Columns:
- name (VARCHAR): Indicator name
- interval (VARCHAR): Data interval (monthly)
- unit (VARCHAR): Unit (percent)
- date (DATE): Data date
- value (NUMERIC): Unemployment rate
- created_at (TIMESTAMP): Record creation time
Usage: Labor market analysis
"""

US_INCOME_STATEMENT_SCHEMA = """
Table: us_income_statement
Description: US company income statement data
Primary Key: (symbol, fiscal_date_ending)
Columns:
- symbol (VARCHAR): Stock ticker
- fiscal_date_ending (DATE): Fiscal date ending
- reported_currency (VARCHAR): Reporting currency
- gross_profit (BIGINT): Gross profit
- total_revenue (BIGINT): Total revenue
- cost_of_revenue (BIGINT): Cost of revenue
- cost_of_goods_and_services_sold (BIGINT): Cost of goods sold
- operating_income (BIGINT): Operating income
- selling_general_and_administrative (BIGINT): SG&A expenses
- research_and_development (BIGINT): R&D expenses
- operating_expenses (BIGINT): Operating expenses
- investment_income_net (BIGINT): Net investment income
- net_interest_income (BIGINT): Net interest income
- interest_income (BIGINT): Interest income
- interest_expense (BIGINT): Interest expense
- non_interest_income (BIGINT): Non-interest income
- other_non_operating_income (BIGINT): Other non-operating income
- depreciation (BIGINT): Depreciation
- depreciation_and_amortization (BIGINT): D&A
- income_before_tax (BIGINT): Income before tax
- income_tax_expense (BIGINT): Income tax expense
- interest_and_debt_expense (BIGINT): Interest and debt expense
- net_income_from_continuing_operations (BIGINT): Net income from continuing ops
- comprehensive_income_net_of_tax (BIGINT): Comprehensive income
- ebit (BIGINT): EBIT
- ebitda (BIGINT): EBITDA
- net_income (BIGINT): Net income
- created_at (TIMESTAMP): Record creation time
Usage: Income statement analysis, profitability metrics
"""

US_BALANCE_SHEET_SCHEMA = """
Table: us_balance_sheet
Description: US company balance sheet data
Primary Key: (symbol, fiscal_date_ending)
Columns:
- symbol (VARCHAR): Stock ticker
- fiscal_date_ending (DATE): Fiscal date ending
- reported_currency (VARCHAR): Reporting currency
- total_assets (BIGINT): Total assets
- total_current_assets (BIGINT): Total current assets
- cash_and_cash_equivalents_at_carrying_value (BIGINT): Cash and equivalents
- cash_and_short_term_investments (BIGINT): Cash and short-term investments
- inventory (BIGINT): Inventory
- current_net_receivables (BIGINT): Current net receivables
- total_non_current_assets (BIGINT): Total non-current assets
- property_plant_equipment (BIGINT): PP&E
- accumulated_depreciation_amortization_ppe (BIGINT): Accumulated depreciation
- intangible_assets (BIGINT): Intangible assets
- intangible_assets_excluding_goodwill (BIGINT): Intangibles ex-goodwill
- goodwill (BIGINT): Goodwill
- investments (BIGINT): Investments
- long_term_investments (BIGINT): Long-term investments
- short_term_investments (BIGINT): Short-term investments
- other_current_assets (BIGINT): Other current assets
- other_non_current_assets (BIGINT): Other non-current assets
- total_liabilities (BIGINT): Total liabilities
- total_current_liabilities (BIGINT): Total current liabilities
- current_accounts_payable (BIGINT): Current accounts payable
- deferred_revenue (BIGINT): Deferred revenue
- current_debt (BIGINT): Current debt
- short_term_debt (BIGINT): Short-term debt
- total_non_current_liabilities (BIGINT): Total non-current liabilities
- capital_lease_obligations (BIGINT): Capital lease obligations
- long_term_debt (BIGINT): Long-term debt
- current_long_term_debt (BIGINT): Current portion of long-term debt
- long_term_debt_noncurrent (BIGINT): Non-current long-term debt
- short_long_term_debt_total (BIGINT): Total short and long-term debt
- other_current_liabilities (BIGINT): Other current liabilities
- other_non_current_liabilities (BIGINT): Other non-current liabilities
- total_shareholder_equity (BIGINT): Total shareholder equity
- treasury_stock (BIGINT): Treasury stock
- retained_earnings (BIGINT): Retained earnings
- common_stock (BIGINT): Common stock
- common_stock_shares_outstanding (BIGINT): Shares outstanding
- created_at (TIMESTAMP): Record creation time
Usage: Balance sheet analysis, financial health assessment
"""

US_CASH_FLOW_SCHEMA = """
Table: us_cash_flow
Description: US company cash flow statement data
Primary Key: (symbol, fiscal_date_ending)
Columns:
- symbol (VARCHAR): Stock ticker
- fiscal_date_ending (DATE): Fiscal date ending
- reported_currency (CHAR): Reporting currency
- operating_cashflow (BIGINT): Operating cash flow
- payments_for_operating_activities (BIGINT): Payments for operating activities
- proceeds_from_operating_activities (BIGINT): Proceeds from operating activities
- change_in_operating_liabilities (BIGINT): Change in operating liabilities
- change_in_operating_assets (BIGINT): Change in operating assets
- depreciation_depletion_and_amortization (BIGINT): DD&A
- capital_expenditures (BIGINT): Capital expenditures
- change_in_receivables (BIGINT): Change in receivables
- change_in_inventory (BIGINT): Change in inventory
- profit_loss (BIGINT): Profit/loss
- cashflow_from_investment (BIGINT): Cash flow from investing
- cashflow_from_financing (BIGINT): Cash flow from financing
- proceeds_from_repayments_of_short_term_debt (BIGINT): Short-term debt repayments
- payments_for_repurchase_of_common_stock (BIGINT): Stock repurchase payments
- payments_for_repurchase_of_equity (BIGINT): Equity repurchase payments
- payments_for_repurchase_of_preferred_stock (BIGINT): Preferred stock repurchase
- dividend_payout (BIGINT): Dividend payout
- dividend_payout_common_stock (BIGINT): Common stock dividends
- dividend_payout_preferred_stock (BIGINT): Preferred stock dividends
- proceeds_from_issuance_of_common_stock (BIGINT): Common stock issuance proceeds
- proceeds_from_issuance_of_long_term_debt_and_capital_securities_net (BIGINT): Long-term debt issuance
- proceeds_from_issuance_of_preferred_stock (BIGINT): Preferred stock issuance
- proceeds_from_repurchase_of_equity (BIGINT): Equity repurchase proceeds
- proceeds_from_sale_of_treasury_stock (BIGINT): Treasury stock sale proceeds
- change_in_cash_and_cash_equivalents (BIGINT): Change in cash
- change_in_exchange_rate (BIGINT): Exchange rate impact
- net_income (BIGINT): Net income
- created_at (TIMESTAMP): Record creation time
Usage: Cash flow analysis, free cash flow calculation
"""

US_EARNINGS_ESTIMATES_SCHEMA = """
Table: us_earnings_estimates
Description: US earnings estimates data
Primary Key: (symbol, estimate_date, horizon)
Columns:
- symbol (VARCHAR): Stock ticker
- estimate_date (DATE): Estimate date
- horizon (VARCHAR): Estimate horizon (e.g., next fiscal year)
- eps_estimate_average (NUMERIC): Average EPS estimate
- eps_estimate_high (NUMERIC): High EPS estimate
- eps_estimate_low (NUMERIC): Low EPS estimate
- eps_estimate_analyst_count (INTEGER): Number of analysts
- eps_estimate_average_7_days_ago (NUMERIC): EPS estimate 7 days ago
- eps_estimate_average_30_days_ago (NUMERIC): EPS estimate 30 days ago
- eps_estimate_average_60_days_ago (NUMERIC): EPS estimate 60 days ago
- eps_estimate_average_90_days_ago (NUMERIC): EPS estimate 90 days ago
- eps_estimate_revision_up_trailing_7_days (INTEGER): Upward revisions 7d
- eps_estimate_revision_down_trailing_7_days (INTEGER): Downward revisions 7d
- eps_estimate_revision_up_trailing_30_days (INTEGER): Upward revisions 30d
- eps_estimate_revision_down_trailing_30_days (INTEGER): Downward revisions 30d
- revenue_estimate_average (NUMERIC): Average revenue estimate
- revenue_estimate_high (NUMERIC): High revenue estimate
- revenue_estimate_low (NUMERIC): Low revenue estimate
- revenue_estimate_analyst_count (INTEGER): Revenue analyst count
- created_at (TIMESTAMP): Record creation time
Usage: Earnings revision analysis, estimate tracking
"""

US_EARNINGS_CALENDAR_SCHEMA = """
Table: us_earnings_calendar
Description: US earnings calendar
Primary Key: (symbol, fiscaldateending)
Columns:
- symbol (VARCHAR): Stock ticker
- name (VARCHAR): Company name
- reportdate (DATE): Report date
- fiscaldateending (DATE): Fiscal date ending
- estimate (NUMERIC): EPS estimate
- currency (VARCHAR): Currency
- created_at (TIMESTAMP): Record creation time
Usage: Earnings event tracking
"""

US_DIVIDENDS_SCHEMA = """
Table: us_dividends
Description: US dividend data
Primary Key: (symbol, ex_dividend_date)
Columns:
- symbol (VARCHAR): Stock ticker
- ex_dividend_date (DATE): Ex-dividend date
- declaration_date (DATE): Declaration date
- record_date (DATE): Record date
- payment_date (DATE): Payment date
- amount (NUMERIC): Dividend amount per share
- created_at (TIMESTAMP): Record creation time
Usage: Dividend analysis, income investing
"""

US_SPLITS_SCHEMA = """
Table: us_splits
Description: US stock split data
Primary Key: (symbol, effective_date)
Columns:
- symbol (VARCHAR): Stock ticker
- effective_date (DATE): Split effective date
- split_factor (NUMERIC): Split ratio
- created_at (TIMESTAMP): Record creation time
Usage: Stock split history tracking
"""

US_NEWS_SCHEMA = """
Table: us_news
Description: US financial news data
Primary Key: (ticker, url, time_published)
Columns:
- title (VARCHAR): News title
- url (TEXT): News URL
- time_published (TIMESTAMP): Publication time
- authors (TEXT[]): Author names
- summary (TEXT): News summary
- banner_image (TEXT): Banner image URL
- source (VARCHAR): News source
- category_within_source (VARCHAR): Category
- source_domain (VARCHAR): Source domain
- topics (JSONB): Topics
- relevance_score (NUMERIC): Relevance score
- overall_sentiment_score (NUMERIC): Overall sentiment score
- overall_sentiment_label (VARCHAR): Sentiment label
- symbol_sentiment (JSONB): Symbol-specific sentiment
- ticker (VARCHAR): Related ticker
- relevance_score_t (NUMERIC): Ticker relevance score
- ticker_sentiment_score (NUMERIC): Ticker sentiment score
- ticker_sentiment_label (VARCHAR): Ticker sentiment label
- created_at (TIMESTAMP): Record creation time
Usage: News sentiment analysis, event-driven analysis
"""

US_INSIDER_TRANSACTIONS_SCHEMA = """
Table: us_insider_transactions
Description: US insider transaction data
Primary Key: (symbol, date, executive)
Columns:
- date (DATE): Transaction date
- symbol (VARCHAR): Stock ticker
- executive (TEXT[]): Insider names
- executive_title (TEXT[]): Insider titles
- security_type (VARCHAR): Security type
- acquisition_or_disposal (VARCHAR): Acquisition or disposal
- shares (NUMERIC): Number of shares
- share_price (NUMERIC): Transaction price
Usage: Insider trading analysis
"""

US_MARKET_REGIME_SCHEMA = """
Table: us_market_regime
Description: US market regime classification
Primary Key: created_at
Columns:
- regime (VARCHAR): Market regime (BULL, NEUTRAL, BEAR)
- vix_proxy (NUMERIC): VIX proxy value
- put_call_ratio (NUMERIC): Put/call ratio
- iv_skew (NUMERIC): IV skew
- spy_return_1m (NUMERIC): SPY 1-month return
- spy_return_3m (NUMERIC): SPY 3-month return
- spy_ma200_distance (NUMERIC): Distance from 200-day MA
- nasdaq_vs_spy_3m (NUMERIC): NASDAQ vs SPY 3-month relative return
- fed_rate (NUMERIC): Federal funds rate
- fed_rate_change_6m (NUMERIC): Fed rate change (6 months)
- cpi_yoy (NUMERIC): CPI year-over-year
- unemployment_rate (NUMERIC): Unemployment rate
- weight_value (NUMERIC): Value factor weight
- weight_quality (NUMERIC): Quality factor weight
- weight_momentum (NUMERIC): Momentum factor weight
- weight_growth (NUMERIC): Growth factor weight
- created_at (TIMESTAMP): Record creation time
Usage: Market regime analysis, factor rotation
"""

US_SECTOR_BENCHMARKS_SCHEMA = """
Table: us_sector_benchmarks
Description: US sector benchmark statistics
Primary Key: (date, sector)
Columns:
- id (SERIAL): ID
- date (DATE): Data date
- sector (VARCHAR): Sector name
- stock_count (INTEGER): Number of stocks
- pe_p25 (NUMERIC): PE 25th percentile
- pe_median (NUMERIC): PE median
- pe_p75 (NUMERIC): PE 75th percentile
- forward_pe_median (NUMERIC): Forward PE median
- peg_median (NUMERIC): PEG median
- ps_median (NUMERIC): PS median
- ev_ebitda_median (NUMERIC): EV/EBITDA median
- gross_margin_p25 (NUMERIC): Gross margin 25th percentile
- gross_margin_median (NUMERIC): Gross margin median
- gross_margin_p75 (NUMERIC): Gross margin 75th percentile
- operating_margin_median (NUMERIC): Operating margin median
- roic_median (NUMERIC): ROIC median
- roe_median (NUMERIC): ROE median
- revenue_growth_median (NUMERIC): Revenue growth median
- eps_growth_median (NUMERIC): EPS growth median
- return_1m_median (NUMERIC): 1-month return median
- return_3m_median (NUMERIC): 3-month return median
- return_6m_median (NUMERIC): 6-month return median
- created_at (TIMESTAMP): Record creation time
Usage: Sector valuation benchmarks, relative value analysis
"""

US_MOVE_INDEX_SCHEMA = """
Table: us_move_index
Description: MOVE Index (bond market volatility)
Primary Key: date
Columns:
- name (VARCHAR): Index name
- interval (VARCHAR): Data interval
- unit (VARCHAR): Unit
- date (DATE): Data date
- value (NUMERIC): Index value
- created_at (TIMESTAMP): Record creation time
Usage: Bond market volatility analysis
"""

US_DOLLAR_INDEX_SCHEMA = """
Table: us_dollar_index
Description: US Dollar Index data
Primary Key: date
Columns:
- name (VARCHAR): Index name
- interval (VARCHAR): Data interval
- date (DATE): Data date
- value (NUMERIC): Index value
- created_at (TIMESTAMP): Record creation time
Usage: Currency strength analysis
"""

US_CREDIT_SPREAD_SCHEMA = """
Table: us_credit_spread
Description: US credit spread data
Primary Key: date
Columns:
- name (VARCHAR): Spread name
- interval (VARCHAR): Data interval
- unit (VARCHAR): Unit
- date (DATE): Data date
- value (NUMERIC): Spread value
- created_at (TIMESTAMP): Record creation time
Usage: Credit risk analysis
"""

US_VIX_SCHEMA = """
Table: us_vix
Description: VIX volatility index data
Primary Key: date
Columns:
- name (VARCHAR): Index name
- interval (VARCHAR): Data interval
- unit (VARCHAR): Unit
- date (DATE): Data date
- value (NUMERIC): VIX value
- created_at (TIMESTAMP): Record creation time
Usage: Market volatility analysis, fear gauge
"""

US_FED_RRP_SCHEMA = """
Table: us_fed_rrp
Description: Federal Reserve Reverse Repo data
Primary Key: date
Columns:
- name (VARCHAR): Indicator name
- interval (VARCHAR): Data interval
- unit (VARCHAR): Unit
- date (DATE): Data date
- value (NUMERIC): RRP value
- created_at (TIMESTAMP): Record creation time
Usage: Liquidity analysis, Fed policy monitoring
"""

US_STOCK_GRADE_SCHEMA = """
Table: us_stock_grade
Description: US stock quant analysis model results
Primary Key: (symbol, date)
Columns:
- stock_name (VARCHAR): Stock name
- symbol (VARCHAR): Stock ticker
- date (DATE): Analysis date
- final_grade (VARCHAR): Investment grade (강력 매수, 매수, 매수 고려, 중립, 매도 고려, 매도, 강력 매도)
- final_score (NUMERIC): Final score (0-100)
- value_score (NUMERIC): Value factor score (0-100)
- quality_score (NUMERIC): Quality factor score (0-100)
- momentum_score (NUMERIC): Momentum factor score (0-100)
- growth_score (NUMERIC): Growth factor score (0-100)
- confidence_score (NUMERIC): Confidence score (0-100)
- var_95 (NUMERIC): Daily VaR 95% (%)
- cvar_95 (NUMERIC): Daily CVaR 95% (%)
- hurst_exponent (NUMERIC): Hurst exponent (0-1)
- var_95_5d (NUMERIC): 5-day VaR 95% (%)
- var_95_20d (NUMERIC): 20-day VaR 95% (%)
- var_95_60d (NUMERIC): 60-day VaR 95% (%)
- var_95_90d (NUMERIC): 90-day VaR 95% (%)
- var_99 (NUMERIC): Daily VaR 99% (%)
- var_99_90d (NUMERIC): 90-day VaR 99% (%)
- value_momentum (NUMERIC): Value factor momentum
- quality_momentum (NUMERIC): Quality factor momentum
- momentum_momentum (NUMERIC): Momentum factor momentum
- growth_momentum (NUMERIC): Growth factor momentum
- industry_rank (INTEGER): Industry rank
- industry_percentile (NUMERIC): Industry percentile (%)
- beta (NUMERIC): Beta coefficient
- volatility_annual (NUMERIC): Annualized volatility (%)
- max_drawdown_1y (NUMERIC): 1-year max drawdown (%)
- risk_profile_text (TEXT): Risk profile interpretation
- risk_recommendation (TEXT): Investor suitability recommendation
- time_series_text (TEXT): Time series interpretation
- signal_overall (TEXT): Overall signal evaluation
- market_state (VARCHAR): Market state classification
- rs_value (NUMERIC): Relative strength value
- rs_rank (TEXT): Relative strength rank
- factor_combination_bonus (INTEGER): Factor combination bonus
- sector_rotation_score (INTEGER): Sector rotation score (0-100)
- sector_momentum (NUMERIC): Sector momentum (%)
- sector_rank (INTEGER): Sector rank
- sector_percentile (NUMERIC): Sector percentile (%)
- value_v2_detail (JSONB): Value factor details JSON
- quality_v2_detail (JSONB): Quality factor details JSON
- momentum_v2_detail (JSONB): Momentum factor details JSON
- growth_v2_detail (JSONB): Growth factor details JSON
- interaction_score (NUMERIC): Factor interaction score (0-100)
- conviction_score (NUMERIC): Conviction score (0-100)
- entry_timing_score (NUMERIC): Entry timing score (0-100)
- score_trend_2w (NUMERIC): 2-week score trend
- price_position_52w (NUMERIC): 52-week price position (%)
- stop_loss_pct (NUMERIC): Stop loss % (negative)
- take_profit_pct (NUMERIC): Take profit % (positive)
- risk_reward_ratio (NUMERIC): Risk/reward ratio
- position_size_pct (NUMERIC): Recommended position size (%)
- atr_pct (NUMERIC): ATR% (14-day)
- scenario_bullish_prob (INTEGER): Bullish scenario probability (%)
- scenario_sideways_prob (INTEGER): Sideways scenario probability (%)
- scenario_bearish_prob (INTEGER): Bearish scenario probability (%)
- scenario_bullish_return (VARCHAR): Bullish return range
- scenario_sideways_return (VARCHAR): Sideways return range
- scenario_bearish_return (VARCHAR): Bearish return range
- scenario_sample_count (INTEGER): Scenario sample count
- buy_triggers (JSONB): Buy trigger conditions
- sell_triggers (JSONB): Sell trigger conditions
- hold_triggers (JSONB): Hold trigger conditions
- iv_percentile (INTEGER): IV percentile (0-100)
- insider_signal (VARCHAR): Insider trading signal
- outlier_risk_score (NUMERIC): Outlier risk score (0-100)
- risk_flag (VARCHAR): Risk flag (EXTREME_RISK, HIGH_RISK, MODERATE_RISK, NORMAL)
- weight_growth (NUMERIC): Growth weight (%)
- weight_momentum (NUMERIC): Momentum weight (%)
- weight_quality (NUMERIC): Quality weight (%)
- weight_value (NUMERIC): Value weight (%)
- sharpe_ratio (NUMERIC): Sharpe ratio
- sortino_ratio (NUMERIC): Sortino ratio
- calmar_ratio (NUMERIC): Calmar ratio
- strategy (JSON): AI investment strategy analysis
- downside_vol (NUMERIC): Downside volatility (%)
- tail_beta (NUMERIC): Tail beta
- corr_spy (NUMERIC): SPY correlation
- cvar_99 (NUMERIC): CVaR 99% (%)
- var_95_ewma (NUMERIC): EWMA VaR 95% (%)
- inv_vol_weight (NUMERIC): Inverse volatility weight
- vol_percentile (INTEGER): Volatility percentile
- corr_sector_avg (NUMERIC): Sector average correlation
- drawdown_duration_avg (NUMERIC): Average drawdown duration (days)
- alt_symbol (VARCHAR): Alternative stock ticker recommendation
- alt_stock_name (VARCHAR): Alternative stock name
- alt_final_grade (VARCHAR): Alternative stock investment grade
- alt_final_score (NUMERIC): Alternative stock final score
- alt_match_type (VARCHAR): Alternative match type (same_sector, similar_score, higher_quality, lower_risk)
- alt_reasons (JSONB): Alternative stock recommendation reasons JSON array
- value_rank (VARCHAR): Value factor rank ('X위' or '공동 X위' format)
- value_percentile (NUMERIC): Value factor percentile (0-100%, 0%=top)
- quality_rank (VARCHAR): Quality factor rank
- quality_percentile (NUMERIC): Quality factor percentile (0-100%)
- momentum_rank (VARCHAR): Momentum factor rank
- momentum_percentile (NUMERIC): Momentum factor percentile (0-100%)
- growth_rank (VARCHAR): Growth factor rank
- growth_percentile (NUMERIC): Growth factor percentile (0-100%)
- created_at (TIMESTAMP): Record creation time
Usage: US stock quant screening, investment grade filtering
"""

US_GDP_SCHEMA = """
Table: us_gdp
Description: US GDP data
Primary Key: date
Columns:
- name (VARCHAR): Indicator name
- interval (VARCHAR): Data interval
- unit (VARCHAR): Unit
- date (DATE): Data date
- value (NUMERIC): GDP value
- created_at (TIMESTAMP): Record creation time
Usage: Economic growth analysis
"""

US_PMI_SCHEMA = """
Table: us_pmi
Description: US PMI (Purchasing Managers Index) data
Primary Key: date
Columns:
- name (VARCHAR): Indicator name
- interval (VARCHAR): Data interval
- unit (VARCHAR): Unit
- date (DATE): Data date
- value (NUMERIC): PMI value
- created_at (TIMESTAMP): Record creation time
Usage: Manufacturing activity analysis
"""

MV_US_SECTOR_DAILY_PERFORMANCE_SCHEMA = """
Table: mv_us_sector_daily_performance
Description: US sector daily performance materialized view
Primary Key: (date, sector_code)
Columns:
- date (DATE): Trading date
- sector_code (VARCHAR): Sector code
- avg_return_30d (NUMERIC): 30-day average return
- stock_count (INTEGER): Number of stocks in sector
- sector_rank (INTEGER): Sector rank by performance
Usage: US sector rotation analysis, sector momentum screening
"""


# =============================================================================
# TABLE SCHEMAS - COMMON TABLES
# =============================================================================

MARKET_INDEX_SCHEMA = """
Table: market_index
Description: Market index data (KOSPI, KOSDAQ, NASDAQ, NYSE)
Primary Key: (exchange, date)
Columns:
- exchange (VARCHAR): Index name (KOSPI, KOSDAQ, NASDAQ, NYSE)
- date (DATE): Trading date
- close (NUMERIC): Closing value
- open (NUMERIC): Opening value
- high (NUMERIC): Day high
- low (NUMERIC): Day low
- change_rate (NUMERIC): Change rate (%)
- change_amount (NUMERIC): Change amount
- volume (BIGINT): Trading volume
- trading_value (BIGINT): Trading value
Usage: Market index queries, benchmark comparison
"""

BOK_INDICATORS_SCHEMA = """
Table: bok_economic_indicators
Description: Bank of Korea economic indicators
Primary Key: (stat_code, time_value, item_code1)
Columns:
- stat_code (VARCHAR): Statistics code
- stat_name (VARCHAR): Indicator name (Base rate, GDP, CPI, Producer Price Index, Consumer Price Index, Export/Import Price Index, Economic Sentiment Index, News Sentiment Index)
- item_code1 (VARCHAR): Item code 1
- item_name1 (VARCHAR): Item name 1
- item_code2 (VARCHAR): Item code 2
- item_name2 (VARCHAR): Item name 2
- item_code3 (VARCHAR): Item code 3
- item_name3 (VARCHAR): Item name 3
- item_code4 (VARCHAR): Item code 4
- item_name4 (VARCHAR): Item name 4
- unit_name (VARCHAR): Unit name
- wgt (NUMERIC): Weight
- cycle (CHAR): Frequency (A=Annual, Q=Quarterly, M=Monthly, D=Daily)
- time_value (DATE): Date
- time_original (VARCHAR): Original time string
- data_value (NUMERIC): Indicator value
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: Korean macroeconomic data queries, economic indicator analysis
"""

EXCHANGE_RATE_SCHEMA = """
Table: exchange_rate
Description: Exchange rate data
Primary Key: (stat_code, time_value, item_code1)
Columns:
- stat_code (VARCHAR): Statistics code
- stat_name (VARCHAR): Indicator name
- item_code1 (VARCHAR): Item code
- item_name1 (VARCHAR): Currency pair (e.g., 'USD/KRW')
- unit_name (VARCHAR): Unit name
- cycle (CHAR): Frequency (A=Annual, Q=Quarterly, M=Monthly, D=Daily)
- time_value (DATE): Date
- time_original (VARCHAR): Original time string
- data_value (NUMERIC): Exchange rate value
- created_at (TIMESTAMP): Record creation time
- updated_at (TIMESTAMP): Last update time
Usage: Currency exchange rate queries
"""

DAILY_RECOMMENDATION_SCHEMA = """
Table: daily_recommendation
Description: Daily curated stock buy recommendations (top picks). Contains both KR and US stocks filtered by country column.
Columns:
- stock_name (VARCHAR): Stock name
- symbol (VARCHAR): Stock code
- date (DATE): Recommendation date
- country (VARCHAR): 'KR' or 'US'
- rank (INTEGER): Recommendation ranking (1 = best)
- final_grade (VARCHAR): Investment grade (매수 고려, 매수, 강력 매수)
- final_score (DECIMAL): Overall quant score (0-100)
- signal_overall (TEXT): Overall signal description
- time_series_text (TEXT): Time series trend summary
- risk_profile_text (TEXT): Risk profile summary
- volatility_annual (NUMERIC): Annual volatility %
- max_drawdown_1y (NUMERIC): 1-year max drawdown %
- var_95 (NUMERIC): Value at Risk 95%
- cvar_95 (NUMERIC): Conditional VaR 95%
- beta (NUMERIC): Market beta
- sector_momentum (NUMERIC): Sector momentum score
- rs_value (NUMERIC): Relative strength value
- rs_rank (TEXT): Relative strength rank category
- industry_rank (INTEGER): Industry ranking
- sector_rank (INTEGER): Sector ranking
- close (DECIMAL): Current closing price
- change_rate (DECIMAL): Daily price change %
Usage Notes:
- ALWAYS filter by country: WHERE country = 'KR' or WHERE country = 'US'
- ALWAYS use latest date: date = (SELECT MAX(date) FROM daily_recommendation WHERE country = '...')
- ORDER BY rank ASC for best recommendations first
"""


# =============================================================================
# SCHEMA COLLECTIONS
# =============================================================================

KR_SCHEMAS = {
    # Core price/quote tables
    "kr_intraday": KR_INTRADAY_SCHEMA,
    "kr_intraday_total": KR_INTRADAY_TOTAL_SCHEMA,
    "kr_intraday_detail": KR_INTRADAY_DETAIL_SCHEMA,
    # Technical indicators
    "kr_indicators": KR_INDICATORS_SCHEMA,
    # Quant analysis
    "kr_stock_grade": KR_STOCK_GRADE_SCHEMA,
    # Investor trading
    "kr_individual_investor_daily_trading": KR_INDIVIDUAL_INVESTOR_DAILY_TRADING_SCHEMA,
    "kr_investor_daily_trading": KR_INVESTOR_DAILY_TRADING_SCHEMA,
    "kr_program_daily_trading": KR_PROGRAM_DAILY_TRADING_SCHEMA,
    # Stock information
    "kr_stock_basic": KR_STOCK_BASIC_SCHEMA,
    "kr_stock_detail": KR_STOCK_DETAIL_SCHEMA,
    # Trading data
    "kr_blocktrades": KR_BLOCKTRADES_SCHEMA,
    "kr_foreign_ownership": KR_FOREIGN_OWNERSHIP_SCHEMA,
    # Financial data (DART)
    "kr_financial_position": KR_FINANCIAL_POSITION_SCHEMA,
    "kr_dividends": KR_DIVIDENDS_SCHEMA,
    "kr_largest_shareholder": KR_LARGEST_SHAREHOLDER_SCHEMA,
    "kr_stockacquisitiondisposal": KR_STOCKACQUISITIONDISPOSAL_SCHEMA,
    "kr_executive": KR_EXECUTIVE_SCHEMA,
    # Research
    "kr_research_reports": KR_RESEARCH_REPORTS_SCHEMA,
    # Benchmark/Sector
    "kr_benchmark_index": KR_BENCHMARK_INDEX_SCHEMA,
    "mv_sector_daily_performance": MV_SECTOR_DAILY_PERFORMANCE_SCHEMA,
}

US_SCHEMAS = {
    # Core price/quote tables
    "us_intraday": US_INTRADAY_SCHEMA,
    "us_daily": US_DAILY_SCHEMA,
    "us_daily_etf": US_DAILY_ETF_SCHEMA,
    "us_weekly": US_WEEKLY_SCHEMA,
    "us_monthly": US_MONTHLY_SCHEMA,
    # Technical indicators
    "us_indicators": US_INDICATORS_SCHEMA,
    # Stock information
    "us_stock_basic": US_STOCK_BASIC_SCHEMA,
    # Quant analysis
    "us_stock_grade": US_STOCK_GRADE_SCHEMA,
    # Options data
    "us_option": US_OPTION_SCHEMA,
    "us_option_daily_summary": US_OPTION_DAILY_SUMMARY_SCHEMA,
    # IPO
    "us_ipo_calendar": US_IPO_CALENDAR_SCHEMA,
    # Financial statements
    "us_income_statement": US_INCOME_STATEMENT_SCHEMA,
    "us_balance_sheet": US_BALANCE_SHEET_SCHEMA,
    "us_cash_flow": US_CASH_FLOW_SCHEMA,
    # Earnings
    "us_earnings_estimates": US_EARNINGS_ESTIMATES_SCHEMA,
    "us_earnings_calendar": US_EARNINGS_CALENDAR_SCHEMA,
    # Dividends and splits
    "us_dividends": US_DIVIDENDS_SCHEMA,
    "us_splits": US_SPLITS_SCHEMA,
    # News and insider
    "us_news": US_NEWS_SCHEMA,
    "us_insider_transactions": US_INSIDER_TRANSACTIONS_SCHEMA,
    # Macro/Economic indicators
    "us_fed_funds_rate": US_FED_FUNDS_RATE_SCHEMA,
    "us_treasury_yield": US_TREASURY_YIELD_SCHEMA,
    "us_cpi": US_CPI_SCHEMA,
    "us_unemployment_rate": US_UNEMPLOYMENT_RATE_SCHEMA,
    "us_gdp": US_GDP_SCHEMA,
    "us_pmi": US_PMI_SCHEMA,
    # Market regime and volatility
    "us_market_regime": US_MARKET_REGIME_SCHEMA,
    "us_vix": US_VIX_SCHEMA,
    "us_move_index": US_MOVE_INDEX_SCHEMA,
    "us_dollar_index": US_DOLLAR_INDEX_SCHEMA,
    "us_credit_spread": US_CREDIT_SPREAD_SCHEMA,
    "us_fed_rrp": US_FED_RRP_SCHEMA,
    # Sector benchmarks
    "us_sector_benchmarks": US_SECTOR_BENCHMARKS_SCHEMA,
    "mv_us_sector_daily_performance": MV_US_SECTOR_DAILY_PERFORMANCE_SCHEMA,
}

COMMON_SCHEMAS = {
    "market_index": MARKET_INDEX_SCHEMA,
    "bok_economic_indicators": BOK_INDICATORS_SCHEMA,
    "exchange_rate": EXCHANGE_RATE_SCHEMA,
    "daily_recommendation": DAILY_RECOMMENDATION_SCHEMA,
}

ALL_SCHEMAS = {**KR_SCHEMAS, **US_SCHEMAS, **COMMON_SCHEMAS}


# =============================================================================
# SQL GENERATION PROMPT TEMPLATE
# =============================================================================

SQL_GENERATION_PROMPT = """You are a PostgreSQL expert specializing in financial data analysis.
Generate accurate SQL queries based on user questions about stock market data.

## Database Schema
{SCHEMA_INFO}

## Term Mapping (Korean to SQL)
{TERM_MAPPING}

## Similar Examples
{FEW_SHOT_EXAMPLES}

## CRITICAL: Korean Stock Table Usage Rules
- kr_intraday: Real-time SNAPSHOT table with NO date column. Use ONLY for "today's current price" queries during market hours.
- kr_intraday_total: HISTORICAL table WITH date column. Use for:
  - Date-based queries (specific date or date range)
  - Multi-day analysis (e.g., "last 5 days", "this week", "compare with yesterday")
  - Period analysis and trends
  - JOINs with kr_indicators (which requires date)
  - ANY query that needs historical data, even during market hours

### When to use which table:
- "Samsung current price?" (during market hours) -> kr_intraday
- "Samsung price for last 5 days?" (during market hours) -> kr_intraday_total
- "Compare today vs yesterday?" (during market hours) -> kr_intraday_total (needs date for comparison)
- "Stocks with RSI < 30?" (during market hours) -> kr_intraday_total JOIN kr_indicators (indicators have date)

### Correct JOIN patterns:
- For historical/date-based queries:
  FROM kr_intraday_total k JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
- For current snapshot with today's indicators:
  FROM kr_intraday k JOIN kr_indicators i ON k.symbol = i.symbol AND i.date = (SELECT MAX(date) FROM kr_indicators)

### Cross-Table Date Handling (CRITICAL for multi-table JOINs)
When JOINing tables with DIFFERENT date semantics, EACH table MUST use its OWN MAX(date):
- kr_financial_position.rcept_dt: Quarterly disclosure date (updates ~4 times/year, e.g., 2025-11)
- kr_individual_investor_daily_trading.date: Daily trading date (updates every trading day, e.g., 2026-02)
- kr_intraday_total.date: Daily price date
- kr_indicators.date: Daily indicator date

CORRECT cross-table query:
SELECT idt.date, idt.symbol, idt.inst_net_volume, idt.foreign_net_volume
FROM kr_individual_investor_daily_trading idt
WHERE idt.symbol IN (
    SELECT symbol FROM kr_financial_position
    WHERE bsns_year = 2024 AND account_nm LIKE '%영업이익%'
)
AND idt.date >= (SELECT MAX(date) FROM kr_individual_investor_daily_trading) - INTERVAL '7 days'
ORDER BY idt.date DESC

WRONG cross-table query (NEVER do this):
SELECT idt.date, fp.rcept_dt, idt.inst_net_volume
FROM kr_individual_investor_daily_trading idt
JOIN kr_financial_position fp ON idt.symbol = fp.symbol
WHERE idt.date >= fp.rcept_dt  -- WRONG: uses quarterly date to filter daily trading data!

### WRONG patterns (NEVER use):
- FROM kr_intraday k JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date  -- kr_intraday has NO date column!
- WHERE date = CURRENT_DATE  -- May return empty on weekends/holidays!

## Latest Data Handling (IMPORTANT)
When user asks for "current", "today", "latest", "now" without specific date:
- For tables WITH date column (kr_intraday_total, us_daily, kr_indicators, etc.):
  - Use MAX(date) subquery to get the most recent trading day
  - Example: WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
- For kr_intraday (NO date column): Just query directly - it's always current data
- NEVER use CURRENT_DATE directly for data queries - weekends/holidays have no trading data
- For US stocks: Always use MAX(date) pattern since us_daily has date column

### Latest data query patterns:
- Single stock latest: WHERE symbol = 'CODE' ORDER BY date DESC LIMIT 1
- All stocks latest day: WHERE date = (SELECT MAX(date) FROM table_name)
- Latest with JOIN: WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)

## CRITICAL: Dividend / Earnings Table Date Handling
- us_dividends, kr_dividends: Historical records. Data is mostly in the PAST, not future.
  - For "highest dividend stocks" ranking: Use 3-month window from MAX date
    WHERE ex_dividend_date >= (SELECT MAX(ex_dividend_date) FROM us_dividends) - INTERVAL '3 months'
  - For "this month's dividends": Use DATE_TRUNC('month', CURRENT_DATE) range
  - NEVER use >= CURRENT_DATE for dividend ranking queries (returns almost no results)
- us_earnings_calendar, us_earnings_estimates: Similar pattern - use MAX date window
- For ranking queries on these tables with LIMIT N:
  - Multiple records per symbol exist (different dates). Deduplicate by symbol.
  - Use: DISTINCT ON (d.symbol) ... ORDER BY d.symbol, d.amount DESC
  - Then wrap in subquery for final ordering: SELECT * FROM (...) sub ORDER BY amount DESC LIMIT N

## Rules
1. Generate ONLY SELECT statements - never INSERT, UPDATE, DELETE, DROP
2. Use exact table and column names from the schema
3. For Korean stocks with date filtering, use kr_intraday_total (NOT kr_intraday)
4. For US stocks, use us_* tables (us_daily, us_indicators, etc.)
5. Always use proper JOINs when combining tables
6. Include appropriate WHERE clauses for filtering
7. Use ORDER BY for ranking queries
8. Use LIMIT for top-N queries (default: 10-20)
9. For latest data, use MAX(date) subquery - NEVER use CURRENT_DATE directly
10. Format numbers without quotes (numeric values)

## CRITICAL: Exclude Suspended/Non-Trading Stocks (ALWAYS APPLY)
All stock listing, ranking, screening, and recommendation queries MUST exclude suspended or non-trading stocks:
- KR: Add `AND final_grade != '거래 정지'` when using kr_stock_grade
- KR: Add `AND open > 0` when using kr_intraday_total or kr_intraday (open = 0 means trading halted)
- US: Add `AND open > 0` when using us_daily (open = 0 means no trading activity)
Only skip this filter when the user explicitly asks about suspended stocks (e.g., "거래정지 종목 알려줘").

## Default Period Rules (IMPORTANT)
- Analysis/forecast requests WITHOUT specific period: Use 90 DAYS of data (approximately 65 trading days)
  - Keywords: '전망', '분석', '추이', '흐름', '동향', 'forecast', 'analysis', 'trend'
  - MUST use date filtering with MAX(date) subquery to get RECENT data, NOT oldest data
  - Example: '삼성전자 주가 전망 분석' -> WHERE symbol = '005930' AND date >= (SELECT MAX(date) FROM kr_intraday_total WHERE symbol = '005930') - INTERVAL '90 days' ORDER BY date ASC
  - Example: '최근 동향 분석해줘' -> WHERE date >= (SELECT MAX(date) FROM table_name) - INTERVAL '90 days' ORDER BY date ASC
  - WRONG: ORDER BY date ASC LIMIT 65 (gets OLDEST data from the beginning of the table!)
  - CORRECT: WHERE date >= MAX(date) - INTERVAL '90 days' ORDER BY date ASC (gets RECENT data)
- Simple lookups (current price, today's data): LIMIT 1 or latest 1 day
- Ranking/sorting queries: LIMIT 10-20 (default)
- Explicit period specified: Use that period
  - '최근 한 달' -> WHERE date >= (SELECT MAX(date) FROM table_name) - INTERVAL '30 days' ORDER BY date ASC
  - '최근 일주일' -> WHERE date >= (SELECT MAX(date) FROM table_name) - INTERVAL '7 days' ORDER BY date ASC
  - '3개월' -> WHERE date >= (SELECT MAX(date) FROM table_name) - INTERVAL '90 days' ORDER BY date ASC

## CRITICAL: Anti-Hallucination Rules
11. NEVER invent or assume table/column names not explicitly listed in the schema above
12. If a required column (e.g., ROE, dividend_rate) is NOT in the schema, do NOT use it
13. If you cannot fulfill the query with available columns, use only what exists and note the limitation
14. ONLY use tables that are explicitly listed in the "Database Schema" section above.
    NEVER invent table names by analogy (e.g., if kr_stock_detail exists, do NOT assume us_stock_detail exists).
    Available tables by market:
    - KR: kr_intraday, kr_intraday_total, kr_intraday_detail, kr_indicators, kr_stock_grade,
          kr_individual_investor_daily_trading, kr_investor_daily_trading, kr_program_daily_trading,
          kr_stock_basic, kr_stock_detail, kr_blocktrades, kr_foreign_ownership,
          kr_financial_position, kr_dividends, kr_largest_shareholder,
          kr_stockacquisitiondisposal, kr_executive, kr_research_reports,
          kr_benchmark_index, mv_sector_daily_performance
    - US: us_intraday, us_daily, us_daily_etf, us_weekly, us_monthly, us_indicators,
          us_stock_basic, us_stock_grade, us_option, us_option_daily_summary,
          us_ipo_calendar, us_income_statement, us_balance_sheet, us_cash_flow,
          us_earnings_estimates, us_earnings_calendar, us_dividends, us_splits,
          us_news, us_insider_transactions, us_fed_funds_rate, us_treasury_yield,
          us_cpi, us_unemployment_rate, us_gdp, us_pmi, us_market_regime, us_vix,
          us_move_index, us_dollar_index, us_credit_spread, us_fed_rrp,
          us_sector_benchmarks, mv_us_sector_daily_performance
    - Common: market_index, bok_economic_indicators, exchange_rate
    NOTE: us_stock_detail does NOT exist. For US stock info use us_stock_basic.
          us_intraday_total does NOT exist. For US price data use us_daily.

## CRITICAL: Sector / Industry / Theme Column Usage
### US Market (us_stock_basic)
- sector: Broad category (14 values, UPPERCASE). Use for "technology stocks", "healthcare sector"
- industry: Specific classification (152 values, UPPERCASE). Use for "semiconductor stocks", "biotech stocks", "software stocks"
- If user mentions specific sub-industry (반도체, semiconductor, biotech, software, bank), use industry NOT sector
- All values are UPPERCASE. Use ILIKE for case-insensitive matching

### KR Market (kr_stock_detail)
- theme: Investment theme (17 values, English). PREFERRED for "관련주" queries (broader coverage)
  - Example: theme = 'Semiconductor' covers 반도체 제조업 + 장비 + 부품 = 138 stocks
- industry: KSIC classification (Korean text). Use for specific industry filtering
  - Example: industry LIKE '%반도체 제조업%' = 75 stocks only
- Rule: "XX 관련주" -> use theme, "XX 제조업" or specific industry -> use industry

### Cross-market (BOTH)
- KR: Use theme for "관련주" (e.g. theme = 'Semiconductor')
- US: Use industry for specific match (e.g. industry ILIKE '%SEMICONDUCTOR%')

## CRITICAL: Divergent/Opposite Query Pattern
15. When user asks for "divergent", "opposite", "extreme difference", or "most different" items:
    - This means selecting BOTH the highest AND lowest values
    - Use UNION ALL pattern: (SELECT ... ORDER BY col DESC LIMIT 1) UNION ALL (SELECT ... ORDER BY col ASC LIMIT 1)
    - Example: "extremely divergent 2 stocks" = TOP 1 (best) + BOTTOM 1 (worst)
    - NEVER interpret this as just "top 2" or "bottom 2"

## CRITICAL: BOTH Market Query Pattern (KR + US Combined Results)
16. When the query applies to BOTH markets (common conditions like RSI, MACD, volume, etc.):
    - Generate a UNION ALL query combining KR and US results
    - Split the LIMIT between markets: KR gets ceil(N/2), US gets floor(N/2)
      (e.g., LIMIT 5 -> KR 3 + US 2, LIMIT 10 -> KR 5 + US 5)
    - The total row count must ALWAYS equal the original requested LIMIT
    - Add 'KR' or 'US' as market column to identify source
    - Use equivalent tables: kr_intraday_total <-> us_daily, kr_indicators <-> us_indicators, kr_stock_grade <-> us_stock_grade
    - Example for "RSI < 30 stocks top 5":
      (SELECT symbol, stock_name, close, 'KR' as market FROM kr_intraday_total k
       JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
       WHERE i.date = (SELECT MAX(date) FROM kr_indicators) AND i.rsi < 30
       ORDER BY i.rsi ASC LIMIT 3)
      UNION ALL
      (SELECT symbol, stock_name, close, 'US' as market FROM us_daily d
       JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
       WHERE i.date = (SELECT MAX(date) FROM us_indicators) AND i.rsi < 30
       ORDER BY i.rsi ASC LIMIT 2)
    - IMPORTANT: Each subquery must have matching column count and compatible types
    - Use stock_name from both tables (both have this column)

## CRITICAL: Time Series vs Aggregation Query Detection
17. Determine if the user wants TIME SERIES data or AGGREGATION data:

### Time Series Keywords (return data with date column for trend visualization):
- Korean: "추이", "흐름", "변화", "추세", "동향", "그래프", "차트", "기간", "한달", "일주일", "최근"
- English: "trend", "history", "over time", "graph", "chart", "period"
- Pattern: SELECT date, value_column FROM table WHERE symbol = 'X' ORDER BY date ASC

### Aggregation Keywords (return grouped/summarized data):
- Korean: "분포", "비율", "구성", "통계", "전체", "몇개", "개수"
- English: "distribution", "ratio", "count", "statistics", "total"
- Pattern: SELECT category, COUNT(*) FROM table GROUP BY category

### Examples:
- "삼성전자 투자등급 추이 보여줘" -> TIME SERIES (date, final_grade for one stock over time)
- "투자등급 분포 보여줘" -> AGGREGATION (final_grade, count grouped by grade)
- "삼성전자 RSI 그래프" -> TIME SERIES (date, rsi for one stock)
- "RSI 30 이하 종목 몇개야" -> AGGREGATION (count of stocks)

### IMPORTANT: When user asks for "graph" or "chart" of a specific stock's data:
- Return TIME SERIES data with date column
- Include the date column in SELECT
- Order by date ASC for proper visualization
- Example: "삼성전자 등급 그래프" -> SELECT date, final_grade FROM kr_stock_grade WHERE symbol = '005930' ORDER BY date ASC

## CRITICAL: Multi-step Analysis Queries
18. When the user asks a multi-step question like "filter -> sort -> pick specific ones -> analyze":
    - The SQL must return the FULL sorted result set, NOT just the final pick
    - The response generator will handle selecting and analyzing specific items from the results
    - Keywords indicating multi-step: "정렬하고 그 중", "순으로 나열하고", "중에서 ... 분석", "추려서 ... 설명"
    - NEVER collapse a multi-step query to LIMIT 1 or LIMIT N when the user explicitly asks for sorting/listing first
    - Example WRONG: "상승률 순으로 정렬하고 그 중 1개 분석" -> ORDER BY gain DESC LIMIT 1 (loses the sorted list!)
    - Example CORRECT: "상승률 순으로 정렬하고 그 중 1개 분석" -> ORDER BY gain DESC (return ALL sorted results)
    - The full list provides context for the analysis and allows the response to show both the ranking AND the detailed analysis
    - Use WITH (CTE) to break multi-step queries into stages:
      Step 1: Initial filter/rank (e.g., foreign net buy top N)
      Step 2: Apply technical conditions (SMA, RSI, volume)
      Step 3: Final output with ORDER BY
    - For cumulative investor data over a period (e.g., 6 months):
      Use SUM(foreign_net_volume) with WHERE date >= MAX(date) - INTERVAL '6 months'
      from kr_individual_investor_daily_trading, GROUP BY symbol
    - For quick 30-day investor summary: use kr_stock_grade.foreign_net_30d / inst_net_30d (pre-calculated)
    - SMA breakout: JOIN kr_indicators, WHERE kr_intraday.close > kr_indicators.sma
    - Volume surge: WHERE volume > avg_volume_20d * 1.5 (moderate) or * 2.0 (strong)

## CRITICAL: Multi-Condition Stock Screening with CTE
20. When the question contains "[SCREENING QUERY" prefix or asks to FIND/FILTER stocks meeting MULTIPLE conditions:
    - Generate a SINGLE SQL with WITH (CTE) chaining all conditions
    - ALWAYS include stock_name in final SELECT (from kr_intraday_total or kr_intraday)
    - Each table uses its OWN MAX(date) subquery (NEVER share dates across tables)

    ### CTE Screening Pattern:
    ```sql
    WITH filtered AS (
        SELECT t.symbol, t.stock_name, t.close, t.per, i.rsi, i.macd, i.macd_signal
        FROM kr_intraday_total t
        JOIN kr_indicators i ON t.symbol = i.symbol
            AND i.date = (SELECT MAX(date) FROM kr_indicators)
        JOIN kr_stock_detail d ON t.symbol = d.symbol
        WHERE t.date = (SELECT MAX(date) FROM kr_intraday_total)
          AND t.per < (SELECT AVG(t2.per) FROM kr_intraday_total t2
                       JOIN kr_stock_detail d2 ON t2.symbol = d2.symbol
                       WHERE d2.industry = d.industry AND t2.date = t.date
                         AND t2.per IS NOT NULL AND t2.per > 0)
          AND i.rsi BETWEEN 30 AND 50
          AND t.per IS NOT NULL AND t.per > 0
    ),
    with_financial AS (
        SELECT DISTINCT fp.symbol FROM kr_financial_position fp
        WHERE fp.account_nm LIKE '%영업이익%' AND fp.sj_div = 'IS'
          AND fp.thstrm_amount > fp.frmtrm_amount
          AND fp.thstrm_amount IS NOT NULL AND fp.frmtrm_amount IS NOT NULL
    ),
    combined AS (
        SELECT f.* FROM filtered f
        WHERE f.symbol IN (SELECT symbol FROM with_financial)
    ),
    ranked AS (
        SELECT c.*, r.target_price,
               ROUND((r.target_price - c.close) / NULLIF(c.close, 0) * 100, 2) AS target_gap_pct
        FROM combined c
        JOIN kr_research_reports r ON c.symbol = r.symbol
            AND r.date = (SELECT MAX(date) FROM kr_research_reports WHERE symbol = c.symbol)
        WHERE r.target_price IS NOT NULL AND r.target_price > 0
    )
    SELECT symbol, stock_name, close, per, rsi, target_price, target_gap_pct
    FROM ranked ORDER BY target_gap_pct DESC LIMIT 5
    ```

    ### CTE Rules:
    - Each table's date: own MAX(date) subquery
    - stock_name: ALWAYS in final SELECT
    - Financial data: filter by sj_div AND account_nm
    - NULL handling: IS NOT NULL for all compared values
    - Maximum 5 CTEs per query

## CRITICAL: Column Selection Rules for Visualization
19. SELECT only the columns necessary for the question:
    - Price trend/chart (추이, 흐름, 그래프): SELECT date, close ONLY
      - Do NOT include open, high, low, volume, change_rate unless explicitly requested
      - Example: "삼성전자 주가 추이" -> SELECT date, close FROM kr_intraday_total WHERE ...
    - Technical indicator analysis (RSI, MACD, 볼린저밴드):
      SELECT date, close, and ONLY the specific indicators mentioned
      - Example: "RSI 분석" -> SELECT date, close, rsi
      - Example: "MACD 분석" -> SELECT date, close, macd, macd_signal
      - Do NOT SELECT all indicators - only those the user asked about
    - Candlestick/OHLC (캔들, 봉차트, 일봉): SELECT date, open, high, low, close, volume
    - Ranking/comparison: SELECT only columns needed for ranking criteria and display
    - WRONG: SELECT date, open, high, low, close, volume, change_rate (for a simple price trend)
    - CORRECT: SELECT date, close (for a simple price trend)

## Common Patterns
- Stock lookup: WHERE symbol = 'CODE'
- Latest data (REQUIRED for date tables): WHERE date = (SELECT MAX(date) FROM table_name)
- Latest per stock: ORDER BY date DESC LIMIT 1
- Historical join: FROM kr_intraday_total k JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
- Current snapshot join: FROM kr_intraday k JOIN kr_indicators i ON k.symbol = i.symbol AND i.date = (SELECT MAX(date) FROM kr_indicators)
- US stock latest: FROM us_daily WHERE date = (SELECT MAX(date) FROM us_daily)
- Ranking: ORDER BY column DESC LIMIT N
- Multiple conditions: Use AND for combining filters
- Date range: WHERE date >= (SELECT MAX(date) FROM table) - INTERVAL '7 days'
- Analysis period (default 90 days): WHERE date >= (SELECT MAX(date) FROM table_name) - INTERVAL '90 days' ORDER BY date ASC
- Time series for graph: SELECT date, column FROM table WHERE symbol = 'X' AND date >= (SELECT MAX(date) FROM table) - INTERVAL '90 days' ORDER BY date ASC

## Conversation Context
{CONVERSATION_CONTEXT}

## Current Question
{USER_QUESTION}

IMPORTANT: If the current question lacks a subject (stock name, conditions, etc.), refer to the conversation context above.
For example, if previous question was about "Samsung Electronics" and current question is "Show it as a graph", understand "it" refers to Samsung Electronics data.

Generate a single, executable PostgreSQL query. Output only the SQL, no explanation.

```sql
"""


def get_schema_for_tables(tables: List[str]) -> str:
    """
    Get schema information for specified tables

    Args:
        tables: List of table names

    Returns:
        Combined schema string
    """
    schemas = []
    for table in tables:
        if table in ALL_SCHEMAS:
            schemas.append(ALL_SCHEMAS[table])
    return "\n".join(schemas) if schemas else "No schema information available."


def get_schema_by_market(market: str) -> str:
    """
    Get all schemas for a market

    Args:
        market: 'KR', 'US', or 'BOTH'

    Returns:
        Combined schema string for the market
    """
    if market == "KR":
        schemas = list(KR_SCHEMAS.values()) + [MARKET_INDEX_SCHEMA]
    elif market == "US":
        schemas = list(US_SCHEMAS.values()) + [MARKET_INDEX_SCHEMA]
    elif market == "BOTH":
        schemas = list(KR_SCHEMAS.values()) + list(US_SCHEMAS.values()) + [MARKET_INDEX_SCHEMA]
    else:
        schemas = list(KR_SCHEMAS.values()) + [MARKET_INDEX_SCHEMA]
    return "\n".join(schemas)


def get_sql_prompt(
    user_question: str,
    schema_info: str,
    term_mapping: str,
    few_shot_examples: str,
    conversation_context: str = ""
) -> str:
    """
    Generate SQL generation prompt

    Args:
        user_question: User's natural language question
        schema_info: Relevant table/column schema
        term_mapping: User term to column mappings
        few_shot_examples: Example question-SQL pairs
        conversation_context: Previous conversation for context (optional)

    Returns:
        Formatted SQL generation prompt
    """
    # Default context message if no history
    if not conversation_context:
        conversation_context = "(No previous conversation in this session)"

    return SQL_GENERATION_PROMPT.format(
        USER_QUESTION=user_question,
        SCHEMA_INFO=schema_info,
        TERM_MAPPING=term_mapping,
        FEW_SHOT_EXAMPLES=few_shot_examples,
        CONVERSATION_CONTEXT=conversation_context
    )


# =============================================================================
# TERM MAPPING FOR PROMPT
# =============================================================================

TERM_MAPPING_TEXT = """
## Price/Quote Terms
- 현재가, 종가 -> close
- 시가 -> open
- 고가 -> high
- 저가 -> low
- 거래량 -> volume
- 거래대금 -> trading_value
- 시총, 시가총액 -> market_cap
- 등락률, 변동률 -> change_rate

## Technical Indicators (in kr_indicators or us_indicators)
- RSI, 알에스아이 -> rsi
- MACD -> macd, macd_signal, macd_hist
- 볼린저밴드 -> real_upper_band, real_middle_band, real_lower_band
- 이평선, 이동평균, SMA -> sma
- EMA, 지수이동평균 -> ema
- VWAP -> vwap, eod_vwap, avg_vwap
- ATR -> atr
- 스토캐스틱 -> slowk, slowd
- MFI -> mfi
- ADX -> adx
- ROC -> roc
- OBV -> obv
- CCI -> cci

## Conditions
- 과매수 -> rsi > 70
- 과매도 -> rsi < 30
- 골든크로스 -> macd > macd_signal
- 데드크로스 -> macd < macd_signal
- 대형주 -> market_cap >= 10000000000000 (10 trillion KRW)
- 중형주 -> market_cap >= 1000000000000 AND market_cap < 10000000000000
- 상한가 -> change_rate >= 29.9
- 하한가 -> change_rate <= -29.9

## Investor Types (Korean market only, from kr_individual_investor_daily_trading)
- 외국인, 외인 -> foreign_net_volume, foreign_net_value
- 기관 -> inst_net_volume, inst_net_value
- 개인, 개미 -> retail_net_volume, retail_net_value
- 순매수 -> net_volume > 0
- 순매도 -> net_volume < 0

## Quant Grades (from kr_stock_grade / us_stock_grade)
- 종합등급, 투자등급 -> final_grade
- 종합점수, 최종점수 -> final_score
- 가치점수 -> value_score
- 퀄리티점수, 품질점수 -> quality_score
- 모멘텀점수 -> momentum_score
- 성장점수 -> growth_score
- 신뢰도점수 -> confidence_score
- 매수 등급 -> final_grade IN ('강력 매수', '매수')
- 강력 매수 -> final_grade = '강력 매수'
- 매수 고려 이상 -> final_grade IN ('강력 매수', '매수', '매수 고려')
- 매도 등급 -> final_grade IN ('매도', '강력 매도')

## Market Index
- 코스피 -> exchange = 'KOSPI'
- 코스닥 -> exchange = 'KOSDAQ'
- 나스닥 -> exchange = 'NASDAQ'
- 뉴욕증시 -> exchange = 'NYSE'

## Sector/Industry/Theme
- 반도체 관련주 (KR) -> kr_stock_detail.theme = 'Semiconductor'
- 반도체 관련주 (US) -> us_stock_basic.industry ILIKE '%SEMICONDUCTOR%' (NOT sector)
- 바이오 관련주 (KR) -> kr_stock_detail.theme = 'Bio_DrugRD'
- 바이오 관련주 (US) -> us_stock_basic.industry ILIKE '%BIOTECH%'
- 소프트웨어 (KR) -> kr_stock_detail.theme = 'IT_Software'
- 소프트웨어 (US) -> us_stock_basic.industry ILIKE '%SOFTWARE%'
- 배터리 (KR) -> kr_stock_detail.theme = 'Battery'
- 기술주/테크 -> us_stock_basic.sector = 'TECHNOLOGY' (broad sector)
- 헬스케어 -> us_stock_basic.sector = 'HEALTHCARE' (broad sector)
"""


def get_default_term_mapping() -> str:
    """Get default term mapping text"""
    return TERM_MAPPING_TEXT
