# services/chat/alpha_ai_model/rag/term_mapper.py
"""
Term Mapper for Alpha AI

Maps user expressions to database columns and business logic.
Supports Korean financial terminology and common expressions.
"""
from typing import List, Dict, Any, Optional, Tuple
from config import logger


class TermMapper:
    """
    Term Mapping Service

    Maps natural language terms to database columns and SQL expressions.
    Handles Korean financial terminology and business logic rules.
    """

    # Static term mappings
    COLUMN_MAPPINGS: Dict[str, Dict[str, Any]] = {
        # Price/Quote terms - Korean
        "현재가": {"column": "close", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "종가": {"column": "close", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "시가": {"column": "open", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "고가": {"column": "high", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "저가": {"column": "low", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "거래량": {"column": "volume", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "거래대금": {"column": "trading_value", "tables": ["kr_intraday", "kr_intraday_total"]},
        "시총": {"column": "market_cap", "tables": ["kr_intraday", "kr_intraday_total", "us_stock_basic"]},
        "시가총액": {"column": "market_cap", "tables": ["kr_intraday", "kr_intraday_total", "us_stock_basic"]},
        "등락률": {"column": "change_rate", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "변동률": {"column": "change_rate", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},

        # Price/Quote terms - English
        "price": {"column": "close", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "close": {"column": "close", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "open": {"column": "open", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "high": {"column": "high", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "low": {"column": "low", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "volume": {"column": "volume", "tables": ["kr_intraday", "kr_intraday_total", "us_daily"]},
        "market cap": {"column": "market_cap", "tables": ["kr_intraday", "kr_intraday_total", "us_stock_basic"]},

        # Valuation metrics - Korean
        "PER": {"column": "per", "tables": ["kr_intraday_total", "kr_intraday_detail", "us_daily", "us_stock_basic"]},
        "PBR": {"column": "pbr", "tables": ["kr_intraday_total", "kr_intraday_detail", "us_daily"]},
        "EPS": {"column": "eps", "tables": ["kr_intraday_total", "kr_intraday_detail", "us_stock_basic"]},
        "ROE": {"column": "roe", "tables": ["kr_intraday_total"]},
        "배당수익률": {"column": "dividend_yield", "tables": ["kr_intraday_total", "kr_intraday_detail"]},
        "배당금": {"column": "dps", "tables": ["kr_intraday_total", "kr_intraday_detail"]},

        # Technical indicators - Korean
        "알에스아이": {"column": "rsi", "tables": ["kr_indicators", "us_indicators"]},
        "볼린저밴드": {"column": "real_upper_band, real_middle_band, real_lower_band", "tables": ["kr_indicators", "us_indicators"]},
        "볼린저": {"column": "real_upper_band, real_middle_band, real_lower_band", "tables": ["kr_indicators", "us_indicators"]},
        "이평선": {"column": "sma, ema", "tables": ["kr_indicators", "us_indicators"]},
        "이동평균": {"column": "sma, ema", "tables": ["kr_indicators", "us_indicators"]},
        "단순이동평균": {"column": "sma", "tables": ["kr_indicators", "us_indicators"]},
        "지수이동평균": {"column": "ema", "tables": ["kr_indicators", "us_indicators"]},

        # Technical indicators - English
        "rsi": {"column": "rsi", "tables": ["kr_indicators", "us_indicators"]},
        "macd": {"column": "macd, macd_signal, macd_hist", "tables": ["kr_indicators", "us_indicators"]},
        "bollinger": {"column": "real_upper_band, real_middle_band, real_lower_band", "tables": ["kr_indicators", "us_indicators"]},
        "sma": {"column": "sma", "tables": ["kr_indicators", "us_indicators"]},
        "ema": {"column": "ema", "tables": ["kr_indicators", "us_indicators"]},
        "vwap": {"column": "vwap", "tables": ["kr_indicators", "us_indicators"]},
        "atr": {"column": "atr", "tables": ["kr_indicators", "us_indicators"]},
        "stochastic": {"column": "slowk, slowd", "tables": ["kr_indicators", "us_indicators"]},
        "mfi": {"column": "mfi", "tables": ["kr_indicators", "us_indicators"]},
        "adx": {"column": "adx", "tables": ["kr_indicators", "us_indicators"]},
        "obv": {"column": "obv", "tables": ["kr_indicators", "us_indicators"]},
        "cci": {"column": "cci", "tables": ["kr_indicators", "us_indicators"]},
        "roc": {"column": "roc", "tables": ["kr_indicators", "us_indicators"]},

        # Investor types - Korean
        "외국인": {"column": "foreign_net_volume, foreign_net_value", "tables": ["kr_individual_investor_daily_trading"]},
        "외인": {"column": "foreign_net_volume, foreign_net_value", "tables": ["kr_individual_investor_daily_trading"]},
        "기관": {"column": "inst_net_volume, inst_net_value", "tables": ["kr_individual_investor_daily_trading"]},
        "개인": {"column": "retail_net_volume, retail_net_value", "tables": ["kr_individual_investor_daily_trading"]},
        "개미": {"column": "retail_net_volume, retail_net_value", "tables": ["kr_individual_investor_daily_trading"]},
        "순매수": {"column": "foreign_net_volume, inst_net_volume, retail_net_volume", "tables": ["kr_individual_investor_daily_trading"]},
        "순매도": {"column": "foreign_net_volume, inst_net_volume, retail_net_volume", "tables": ["kr_individual_investor_daily_trading"]},
        "외국인지분율": {"column": "foreign_rate", "tables": ["kr_foreign_ownership"]},
        "외국인보유": {"column": "foreign_ownership", "tables": ["kr_foreign_ownership"]},

        # Quant grades - Korean (corrected column names)
        "종합등급": {"column": "final_grade", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "투자등급": {"column": "final_grade", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "종합점수": {"column": "final_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "최종점수": {"column": "final_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "가치점수": {"column": "value_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "품질점수": {"column": "quality_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "퀄리티점수": {"column": "quality_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "모멘텀점수": {"column": "momentum_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "성장점수": {"column": "growth_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "신뢰도점수": {"column": "confidence_score", "tables": ["kr_stock_grade", "us_stock_grade"]},

        # Quant grades - English (corrected column names)
        "grade": {"column": "final_grade", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "score": {"column": "final_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "value score": {"column": "value_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "quality score": {"column": "quality_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "momentum score": {"column": "momentum_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "growth score": {"column": "growth_score", "tables": ["kr_stock_grade", "us_stock_grade"]},

        # Risk metrics - Korean
        "베타": {"column": "beta", "tables": ["kr_stock_grade", "us_stock_grade", "us_stock_basic"]},
        "변동성": {"column": "volatility_annual", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "연변동성": {"column": "volatility_annual", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "최대낙폭": {"column": "max_drawdown_1y", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "MDD": {"column": "max_drawdown_1y", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "VaR": {"column": "var_95", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "샤프비율": {"column": "sharpe_ratio", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "소르티노비율": {"column": "sortino_ratio", "tables": ["kr_stock_grade", "us_stock_grade"]},

        # Sector/Industry - Korean
        "업종": {"column": "industry", "tables": ["kr_stock_detail", "us_stock_basic"]},
        "섹터": {"column": "sector", "tables": ["us_stock_basic"]},
        "테마": {"column": "theme", "tables": ["kr_stock_detail"]},
        "관련주": {"column": "theme", "tables": ["kr_stock_detail"]},
        "반도체": {"column": "theme, industry", "tables": ["kr_stock_detail"]},
        "semiconductor": {"column": "industry", "tables": ["us_stock_basic"]},
        "바이오": {"column": "theme, industry", "tables": ["kr_stock_detail"]},
        "biotech": {"column": "industry", "tables": ["us_stock_basic"]},
        "소프트웨어": {"column": "theme, industry", "tables": ["kr_stock_detail"]},
        "배터리": {"column": "theme", "tables": ["kr_stock_detail"]},
        "기술주": {"column": "sector", "tables": ["us_stock_basic"]},
        "헬스케어": {"column": "sector", "tables": ["us_stock_basic"]},

        # US Options - Korean
        "풋콜비율": {"column": "total_put_volume / total_call_volume", "tables": ["us_option_daily_summary"]},
        "내재변동성": {"column": "avg_implied_volatility", "tables": ["us_option_daily_summary"]},
        "IV": {"column": "implied_volatility", "tables": ["us_option"]},
        "감마익스포저": {"column": "net_gex", "tables": ["us_option_daily_summary"]},

        # US Financial statements
        "매출": {"column": "total_revenue", "tables": ["us_income_statement"]},
        "영업이익": {"column": "operating_income", "tables": ["us_income_statement"]},
        "순이익": {"column": "net_income", "tables": ["us_income_statement", "us_cash_flow"]},
        "EBITDA": {"column": "ebitda", "tables": ["us_income_statement", "us_stock_basic"]},
        "자산": {"column": "total_assets", "tables": ["us_balance_sheet"]},
        "부채": {"column": "total_liabilities", "tables": ["us_balance_sheet"]},
        "자본": {"column": "total_shareholder_equity", "tables": ["us_balance_sheet"]},
        "현금흐름": {"column": "operating_cashflow", "tables": ["us_cash_flow"]},

        # US Macro indicators
        "금리": {"column": "value", "tables": ["us_fed_funds_rate", "us_treasury_yield"]},
        "국채수익률": {"column": "value", "tables": ["us_treasury_yield"]},
        "CPI": {"column": "value", "tables": ["us_cpi"]},
        "실업률": {"column": "value", "tables": ["us_unemployment_rate"]},
        "GDP": {"column": "value", "tables": ["us_gdp"]},
        "PMI": {"column": "value", "tables": ["us_pmi"]},
        "VIX": {"column": "value", "tables": ["us_vix"]},
        "달러인덱스": {"column": "value", "tables": ["us_dollar_index"]},

        # Market index
        "코스피": {"column": "exchange", "value": "KOSPI", "tables": ["market_index"]},
        "코스닥": {"column": "exchange", "value": "KOSDAQ", "tables": ["market_index"]},
        "나스닥": {"column": "exchange", "value": "NASDAQ", "tables": ["market_index"]},
        "뉴욕증시": {"column": "exchange", "value": "NYSE", "tables": ["market_index"]},

        # Research reports
        "목표가": {"column": "target_price", "tables": ["kr_research_reports"]},
        "투자의견": {"column": "investment_opinion", "tables": ["kr_research_reports"]},
        "애널리스트": {"column": "securities_firm", "tables": ["kr_research_reports"]},

        # Block trades
        "대량매매": {"column": "block_volume", "tables": ["kr_blocktrades"]},
        "블록딜": {"column": "block_volume", "tables": ["kr_blocktrades"]},

        # Conviction and risk metrics (new columns)
        "확신도점수": {"column": "conviction_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "확신도": {"column": "conviction_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "conviction": {"column": "conviction_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "이상치위험점수": {"column": "outlier_risk_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "ORS": {"column": "outlier_risk_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "아웃라이어리스크": {"column": "outlier_risk_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "위험등급": {"column": "risk_flag", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "리스크플래그": {"column": "risk_flag", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "risk flag": {"column": "risk_flag", "tables": ["kr_stock_grade", "us_stock_grade"]},

        # Alternative stock recommendation
        "대안종목": {"column": "alt_symbol, alt_stock_name, alt_final_grade, alt_final_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "대체종목": {"column": "alt_symbol, alt_stock_name, alt_final_grade, alt_final_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "대안추천": {"column": "alt_symbol, alt_stock_name, alt_final_grade, alt_final_score, alt_reasons", "tables": ["kr_stock_grade", "us_stock_grade"]},

        # Factor rank/percentile mappings
        "가치순위": {"column": "value_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "가치백분위": {"column": "value_percentile", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "품질순위": {"column": "quality_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "품질백분위": {"column": "quality_percentile", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "퀄리티순위": {"column": "quality_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "퀄리티백분위": {"column": "quality_percentile", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "모멘텀순위": {"column": "momentum_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "모멘텀백분위": {"column": "momentum_percentile", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "성장순위": {"column": "growth_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "성장백분위": {"column": "growth_percentile", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "value rank": {"column": "value_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "quality rank": {"column": "quality_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "momentum rank": {"column": "momentum_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "growth rank": {"column": "growth_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},

        # KR Financial statements (kr_financial_position)
        "재무제표": {"column": "*", "tables": ["kr_financial_position"]},
        "당기금액": {"column": "thstrm_amount", "tables": ["kr_financial_position"]},
        "전기금액": {"column": "frmtrm_amount", "tables": ["kr_financial_position"]},

        # KR Largest shareholder (kr_largest_shareholder)
        "최대주주": {"column": "nm", "tables": ["kr_largest_shareholder"]},
        "지분율": {"column": "trmend_posesn_stock_qota_rt", "tables": ["kr_largest_shareholder"]},

        # KR Treasury stock (kr_stockacquisitiondisposal)
        "자기주식": {"column": "*", "tables": ["kr_stockacquisitiondisposal"]},
        "자사주": {"column": "*", "tables": ["kr_stockacquisitiondisposal"]},

        # KR Executive (kr_executive)
        "임원": {"column": "*", "tables": ["kr_executive"]},
        "대표이사": {"column": "nm", "tables": ["kr_executive"]},

        # KR Research reports - supplement (kr_research_reports)
        "리포트": {"column": "*", "tables": ["kr_research_reports"]},

        # KR Foreign ownership - supplement (kr_foreign_ownership)
        "외국인한도": {"column": "foreign_limit", "tables": ["kr_foreign_ownership"]},

        # KR Benchmark/Sector
        "벤치마크": {"column": "*", "tables": ["kr_benchmark_index"]},
        "섹터성과": {"column": "*", "tables": ["mv_sector_daily_performance", "mv_us_sector_daily_performance"]},

        # US Financial statements - table-level mappings
        "손익계산서": {"column": "*", "tables": ["us_income_statement"]},
        "재무상태표": {"column": "*", "tables": ["us_balance_sheet"]},
        "현금흐름표": {"column": "*", "tables": ["us_cash_flow"]},

        # Dividend - supplement
        "배당": {"column": "amount", "tables": ["us_dividends"]},
        "배당락일": {"column": "ex_dividend_date", "tables": ["us_dividends"]},

        # US Options - supplement
        "옵션": {"column": "*", "tables": ["us_option", "us_option_daily_summary"]},
        "콜옵션": {"column": "total_call_volume", "tables": ["us_option_daily_summary"]},
        "풋옵션": {"column": "total_put_volume", "tables": ["us_option_daily_summary"]},
        "델타": {"column": "delta", "tables": ["us_option"]},
        "감마": {"column": "gamma", "tables": ["us_option"]},

        # US Insider transactions
        "내부자": {"column": "*", "tables": ["us_insider_transactions"]},
        "내부자거래": {"column": "*", "tables": ["us_insider_transactions"]},

        # US Macro indicators - supplement
        "연방금리": {"column": "value", "tables": ["us_fed_funds_rate"]},
        "국채금리": {"column": "value", "tables": ["us_treasury_yield"]},
        "물가": {"column": "value", "tables": ["us_cpi"]},

        # US Market indicators - supplement
        "공포지수": {"column": "value", "tables": ["us_vix"]},
        "무브지수": {"column": "value", "tables": ["us_move_index"]},
        "신용스프레드": {"column": "value", "tables": ["us_credit_spread"]},

        # US Earnings
        "실적": {"column": "*", "tables": ["us_earnings_estimates", "us_earnings_calendar"]},
        "eps전망": {"column": "eps_estimate_average", "tables": ["us_earnings_estimates"]},
        "실적전망": {"column": "eps_estimate_average", "tables": ["us_earnings_estimates"]},
        "실적발표": {"column": "*", "tables": ["us_earnings_calendar"]},

        # Quant new columns (kr_stock_grade, us_stock_grade)
        "칼마비율": {"column": "calmar_ratio", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "손절가": {"column": "stop_loss_pct", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "익절가": {"column": "take_profit_pct", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "진입타이밍": {"column": "entry_timing_score", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "섹터순위": {"column": "sector_rank", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "리스크프로파일": {"column": "risk_profile_text", "tables": ["kr_stock_grade", "us_stock_grade"]},
        "시나리오": {"column": "scenario_bullish_prob, scenario_bearish_prob", "tables": ["kr_stock_grade", "us_stock_grade"]},

        # US IPO
        "ipo": {"column": "*", "tables": ["us_ipo_calendar"]},
        "상장예정": {"column": "*", "tables": ["us_ipo_calendar"]},

        # US Stock splits
        "주식분할": {"column": "*", "tables": ["us_splits"]},
        "액면분할": {"column": "split_factor", "tables": ["us_splits"]},

        # US News
        "뉴스": {"column": "*", "tables": ["us_news"]},
        "sentiment": {"column": "overall_sentiment_score", "tables": ["us_news"]},

        # Exchange Rate
        "환율": {"column": "data_value", "tables": ["exchange_rate"]},
        "원달러": {"column": "data_value", "tables": ["exchange_rate"]},
        "원엔": {"column": "data_value", "tables": ["exchange_rate"]},

        # Korean Economic Indicators (BOK)
        "경제지표": {"column": "data_value", "tables": ["bok_economic_indicators"]},
        "기준금리": {"column": "data_value", "tables": ["bok_economic_indicators"]},
        "한국은행": {"column": "data_value", "tables": ["bok_economic_indicators"]},
        "인플레이션": {"column": "value", "tables": ["us_cpi"]},

        # Program Trading
        "프로그램매매": {"column": "net_buy_value", "tables": ["kr_program_daily_trading"]},
        "프로그램": {"column": "net_buy_value", "tables": ["kr_program_daily_trading"]},
        "차익거래": {"column": "net_buy_value", "tables": ["kr_program_daily_trading"]},
        "비차익거래": {"column": "net_buy_value", "tables": ["kr_program_daily_trading"]},

        # Multi-Timeframe
        "주간": {"column": "*", "tables": ["us_weekly"]},
        "월간": {"column": "*", "tables": ["us_monthly"]},
        "제조업지수": {"column": "value", "tables": ["us_pmi"]},
    }

    # Business logic mappings (term -> SQL condition)
    LOGIC_MAPPINGS: Dict[str, Dict[str, Any]] = {
        # RSI conditions
        "과매수": {
            "sql": "rsi > 70",
            "description": "RSI above 70 (overbought)",
            "tables": ["kr_indicators", "us_indicators"]
        },
        "과매도": {
            "sql": "rsi < 30",
            "description": "RSI below 30 (oversold)",
            "tables": ["kr_indicators", "us_indicators"]
        },

        # MACD conditions (corrected - using actual column names)
        "macd 골든크로스": {
            "sql": "macd > macd_signal",
            "description": "MACD above signal line",
            "tables": ["kr_indicators", "us_indicators"]
        },
        "macd 데드크로스": {
            "sql": "macd < macd_signal",
            "description": "MACD below signal line",
            "tables": ["kr_indicators", "us_indicators"]
        },
        "골든크로스": {
            "sql": "macd > macd_signal",
            "description": "MACD golden cross",
            "tables": ["kr_indicators", "us_indicators"]
        },
        "데드크로스": {
            "sql": "macd < macd_signal",
            "description": "MACD dead cross",
            "tables": ["kr_indicators", "us_indicators"]
        },

        # Bollinger Band conditions (corrected column names)
        "볼린저 상단돌파": {
            "sql": "close > real_upper_band",
            "description": "Price above upper Bollinger Band",
            "tables": ["kr_indicators", "us_indicators"]
        },
        "볼린저 하단돌파": {
            "sql": "close < real_lower_band",
            "description": "Price below lower Bollinger Band",
            "tables": ["kr_indicators", "us_indicators"]
        },

        # Market cap classifications (Korean)
        "대형주": {
            "sql": "market_cap >= 10000000000000",
            "description": "Market cap >= 10 trillion KRW",
            "tables": ["kr_intraday", "kr_intraday_total"]
        },
        "중형주": {
            "sql": "market_cap >= 1000000000000 AND market_cap < 10000000000000",
            "description": "Market cap 1-10 trillion KRW",
            "tables": ["kr_intraday", "kr_intraday_total"]
        },
        "소형주": {
            "sql": "market_cap < 1000000000000",
            "description": "Market cap < 1 trillion KRW",
            "tables": ["kr_intraday", "kr_intraday_total"]
        },

        # US Market cap classifications
        "대형주 미국": {
            "sql": "market_cap >= 10000000000",
            "description": "Market cap >= 10 billion USD (Large cap)",
            "tables": ["us_stock_basic"]
        },
        "중형주 미국": {
            "sql": "market_cap >= 2000000000 AND market_cap < 10000000000",
            "description": "Market cap 2-10 billion USD (Mid cap)",
            "tables": ["us_stock_basic"]
        },

        # Price limits (Korean market)
        "상한가": {
            "sql": "change_rate >= 29.9",
            "description": "Upper price limit (+30%)",
            "tables": ["kr_intraday", "kr_intraday_total"]
        },
        "하한가": {
            "sql": "change_rate <= -29.9",
            "description": "Lower price limit (-30%)",
            "tables": ["kr_intraday", "kr_intraday_total"]
        },

        # Volume conditions (corrected - using actual column names)
        "거래량 급증": {
            "sql": "volume > avg_volume_5d * 2",
            "description": "Volume > 2x 5-day average",
            "tables": ["kr_intraday", "kr_intraday_total"]
        },
        "거래대금 급증": {
            "sql": "trading_value > avg_trading_value_5d * 2",
            "description": "Trading value > 2x 5-day average",
            "tables": ["kr_intraday", "kr_intraday_total"]
        },

        # Investor flow conditions
        "외국인 순매수": {
            "sql": "foreign_net_volume > 0",
            "description": "Foreign net buying",
            "tables": ["kr_individual_investor_daily_trading"]
        },
        "외국인 순매도": {
            "sql": "foreign_net_volume < 0",
            "description": "Foreign net selling",
            "tables": ["kr_individual_investor_daily_trading"]
        },
        "기관 순매수": {
            "sql": "inst_net_volume > 0",
            "description": "Institution net buying",
            "tables": ["kr_individual_investor_daily_trading"]
        },
        "기관 순매도": {
            "sql": "inst_net_volume < 0",
            "description": "Institution net selling",
            "tables": ["kr_individual_investor_daily_trading"]
        },

        # Quant grade conditions (Korean grade values)
        # Grades: 강력 매수, 매수, 매수 고려, 중립, 매도 고려, 매도, 강력 매도
        "매수등급": {
            "sql": "final_grade IN ('강력 매수', '매수')",
            "description": "Buy grade (Strong Buy or Buy)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "매수 이상": {
            "sql": "final_grade IN ('강력 매수', '매수')",
            "description": "Buy grade or higher",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "매수 고려 이상": {
            "sql": "final_grade IN ('강력 매수', '매수', '매수 고려')",
            "description": "Buy Consider or higher",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "강력 매수": {
            "sql": "final_grade = '강력 매수'",
            "description": "Strong Buy grade",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "매수": {
            "sql": "final_grade IN ('강력 매수', '매수')",
            "description": "Buy grade (Strong Buy or Buy)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "매도등급": {
            "sql": "final_grade IN ('매도', '강력 매도')",
            "description": "Sell grade (Sell or Strong Sell)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "중립": {
            "sql": "final_grade = '중립'",
            "description": "Neutral grade",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },

        # Factor score conditions
        "고가치": {
            "sql": "value_score >= 70",
            "description": "High value score (>=70)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "고품질": {
            "sql": "quality_score >= 70",
            "description": "High quality score (>=70)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "고모멘텀": {
            "sql": "momentum_score >= 70",
            "description": "High momentum score (>=70)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "고성장": {
            "sql": "growth_score >= 70",
            "description": "High growth score (>=70)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },

        # Risk conditions
        "저변동성": {
            "sql": "volatility_annual < 30",
            "description": "Low volatility (<30% annual)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "고변동성": {
            "sql": "volatility_annual >= 50",
            "description": "High volatility (>=50% annual)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "저베타": {
            "sql": "beta < 1",
            "description": "Low beta (<1)",
            "tables": ["kr_stock_grade", "us_stock_grade", "us_stock_basic"]
        },
        "고베타": {
            "sql": "beta >= 1.5",
            "description": "High beta (>=1.5)",
            "tables": ["kr_stock_grade", "us_stock_grade", "us_stock_basic"]
        },

        # Dividend conditions
        "고배당": {
            "sql": "dividend_yield >= 3",
            "description": "High dividend yield (>=3%)",
            "tables": ["kr_intraday_total", "kr_intraday_detail"]
        },
        "배당주": {
            "sql": "dividend_yield > 0",
            "description": "Dividend paying stock",
            "tables": ["kr_intraday_total", "kr_intraday_detail"]
        },

        # Valuation conditions
        "저PER": {
            "sql": "per > 0 AND per < 10",
            "description": "Low PER (<10)",
            "tables": ["kr_intraday_total", "kr_intraday_detail", "us_daily", "us_stock_basic"]
        },
        "저PBR": {
            "sql": "pbr > 0 AND pbr < 1",
            "description": "Low PBR (<1)",
            "tables": ["kr_intraday_total", "kr_intraday_detail", "us_daily"]
        },

        # Foreign ownership
        "외국인 한도소진": {
            "sql": "foreign_rate_limit >= 90",
            "description": "Foreign ownership limit near exhaustion (>=90%)",
            "tables": ["kr_foreign_ownership"]
        },

        # US Options conditions
        "풋콜비율 높음": {
            "sql": "total_put_volume > total_call_volume * 1.5",
            "description": "High put/call ratio (>1.5)",
            "tables": ["us_option_daily_summary"]
        },
        "콜풋비율 높음": {
            "sql": "total_call_volume > total_put_volume * 1.5",
            "description": "High call/put ratio (>1.5)",
            "tables": ["us_option_daily_summary"]
        },

        # Risk flag conditions (new)
        "고위험": {
            "sql": "risk_flag IN ('HIGH_RISK', 'EXTREME_RISK')",
            "description": "High risk stocks (ORS >= 60)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "위험높음": {
            "sql": "risk_flag IN ('HIGH_RISK', 'EXTREME_RISK')",
            "description": "High risk stocks (ORS >= 60)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "저위험": {
            "sql": "risk_flag = 'NORMAL'",
            "description": "Low risk stocks (ORS < 40)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "안전": {
            "sql": "risk_flag = 'NORMAL'",
            "description": "Safe stocks (ORS < 40)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "극단위험": {
            "sql": "risk_flag = 'EXTREME_RISK'",
            "description": "Extreme risk stocks (ORS >= 80)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "초고위험": {
            "sql": "risk_flag = 'EXTREME_RISK'",
            "description": "Extreme risk stocks (ORS >= 80)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },

        # Conviction score conditions (new)
        "고확신": {
            "sql": "conviction_score >= 70",
            "description": "High conviction stocks (score >= 70)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "확신높음": {
            "sql": "conviction_score >= 70",
            "description": "High conviction stocks (score >= 70)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "저확신": {
            "sql": "conviction_score < 40",
            "description": "Low conviction stocks (score < 40)",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },

        # Alternative stock conditions (new)
        "대안있음": {
            "sql": "alt_symbol IS NOT NULL",
            "description": "Stocks with alternative recommendations",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },

        # Factor percentile conditions
        "가치상위": {
            "sql": "value_percentile <= 20",
            "description": "Top 20% value factor",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "품질상위": {
            "sql": "quality_percentile <= 20",
            "description": "Top 20% quality factor",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "모멘텀상위": {
            "sql": "momentum_percentile <= 20",
            "description": "Top 20% momentum factor",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },
        "성장상위": {
            "sql": "growth_percentile <= 20",
            "description": "Top 20% growth factor",
            "tables": ["kr_stock_grade", "us_stock_grade"]
        },

        # Put/Call ratio - supplement
        "풋콜비율 낮음": {
            "sql": "total_put_volume / NULLIF(total_call_volume, 0) < 0.7",
            "description": "Put/Call ratio < 0.7 (bullish sentiment)",
            "tables": ["us_option_daily_summary"]
        },

        # Insider trading conditions
        "내부자 매수": {
            "sql": "acquisition_or_disposal = 'A'",
            "description": "Insider acquisition",
            "tables": ["us_insider_transactions"]
        },
        "내부자 매도": {
            "sql": "acquisition_or_disposal = 'D'",
            "description": "Insider disposal",
            "tables": ["us_insider_transactions"]
        },

        # VIX fear conditions
        "공포 높음": {
            "sql": "value > 30",
            "description": "VIX above 30 (high fear)",
            "tables": ["us_vix"]
        },
        "공포 낮음": {
            "sql": "value < 15",
            "description": "VIX below 15 (low fear / complacency)",
            "tables": ["us_vix"]
        },

        # Program trading conditions
        "프로그램 순매수": {
            "sql": "net_buy_value > 0",
            "description": "Program trading net buying",
            "tables": ["kr_program_daily_trading"]
        },
        "프로그램 순매도": {
            "sql": "net_buy_value < 0",
            "description": "Program trading net selling",
            "tables": ["kr_program_daily_trading"]
        },
    }

    # Synonym mappings for fuzzy matching
    SYNONYMS: Dict[str, List[str]] = {
        "거래대금": ["거래금액", "매매대금", "거래액"],
        "거래량": ["거래수량", "매매량", "볼륨"],
        "시가총액": ["시총", "시장가치", "마켓캡"],
        "외국인": ["외인", "외국인투자자", "포린"],
        "기관": ["기관투자자", "기관투자"],
        "개인": ["개미", "개인투자자", "리테일"],
        "골든크로스": ["황금교차", "golden cross"],
        "데드크로스": ["사망교차", "dead cross"],
        "과매수": ["과열", "overbought"],
        "과매도": ["침체", "oversold"],
        "재무제표": ["재무정보", "재무", "financial statements"],
        "배당": ["배당금", "dividend", "dividends"],
        "내부자": ["인사이더", "insider", "내부자거래"],
        "옵션": ["파생상품", "option", "options"],
        "금리": ["이자율", "interest rate", "기준금리"],
        "vix": ["빅스", "공포지수", "변동성지수", "fear index"],
        "실적": ["어닝스", "earnings", "실적발표"],
        "ipo": ["기업공개", "상장", "신규상장"],
    }

    def __init__(self):
        """Initialize TermMapper"""
        self.column_mappings = self.COLUMN_MAPPINGS
        self.logic_mappings = self.LOGIC_MAPPINGS
        self.synonyms = self.SYNONYMS
        self._build_synonym_index()
        logger.info("[TermMapper] Initialized with enhanced mappings")

    def _build_synonym_index(self) -> None:
        """Build reverse synonym index for lookup"""
        self.synonym_index = {}
        for canonical, synonyms in self.synonyms.items():
            for syn in synonyms:
                self.synonym_index[syn.lower()] = canonical

    def normalize_term(self, term: str) -> str:
        """
        Normalize term to canonical form

        Args:
            term: User term

        Returns:
            Canonical term
        """
        term_lower = term.lower().strip()

        # Check synonym index
        if term_lower in self.synonym_index:
            return self.synonym_index[term_lower]

        return term_lower

    def find_column_mapping(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Find column mapping for a term

        Args:
            term: User term to look up

        Returns:
            Mapping dictionary or None
        """
        # Normalize term
        normalized = self.normalize_term(term)

        # Exact match
        if normalized in self.column_mappings:
            return self.column_mappings[normalized]

        # Case-insensitive match
        for key, mapping in self.column_mappings.items():
            if key.lower() == normalized:
                return mapping

        # Partial match
        for key, mapping in self.column_mappings.items():
            if key.lower() in normalized or normalized in key.lower():
                return mapping

        return None

    def find_logic_mapping(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Find business logic mapping for a term

        Args:
            term: User term

        Returns:
            Logic mapping or None
        """
        term_lower = term.lower().strip()

        # Exact match
        if term_lower in self.logic_mappings:
            return self.logic_mappings[term_lower]

        # Partial match
        for key, mapping in self.logic_mappings.items():
            if key in term_lower or term_lower in key:
                return mapping

        return None

    def extract_terms(self, query: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Extract all mapped terms from query

        Args:
            query: User query

        Returns:
            List of (term, type, mapping) tuples
        """
        query_lower = query.lower()
        found = []

        # Check column mappings
        for term, mapping in self.column_mappings.items():
            if term.lower() in query_lower:
                found.append((term, "column", mapping))

        # Check logic mappings
        for term, mapping in self.logic_mappings.items():
            if term.lower() in query_lower:
                found.append((term, "logic", mapping))

        return found

    def get_columns_for_query(self, query: str, market: str = "KR") -> List[str]:
        """
        Get relevant column names for query

        Args:
            query: User query
            market: Market filter

        Returns:
            List of column names
        """
        terms = self.extract_terms(query)
        columns = set()

        table_prefix = "kr_" if market == "KR" else "us_"

        for term, term_type, mapping in terms:
            if term_type == "column" and "column" in mapping:
                # Check if table matches market
                tables = mapping.get("tables", [])
                if any(t.startswith(table_prefix) or t in ["market_index"] for t in tables):
                    cols = mapping["column"].split(", ")
                    columns.update(cols)

        return list(columns)

    def get_sql_conditions(self, query: str, market: str = "KR") -> List[Dict[str, str]]:
        """
        Get SQL conditions from business logic terms

        Args:
            query: User query
            market: Market filter

        Returns:
            List of condition dictionaries
        """
        terms = self.extract_terms(query)
        conditions = []

        table_prefix = "kr_" if market == "KR" else "us_"

        for term, term_type, mapping in terms:
            if term_type == "logic" and "sql" in mapping:
                # Check if table matches market
                tables = mapping.get("tables", [])
                if any(t.startswith(table_prefix) for t in tables):
                    conditions.append({
                        "term": term,
                        "sql": mapping["sql"],
                        "description": mapping.get("description", ""),
                        "tables": tables
                    })

        return conditions

    def format_for_prompt(self, query: str, market: str = "KR") -> str:
        """
        Format term mappings for inclusion in prompt

        Args:
            query: User query
            market: Market filter

        Returns:
            Formatted string for prompt
        """
        terms = self.extract_terms(query)

        if not terms:
            return "No specific term mappings found."

        lines = ["## Detected Terms"]

        columns = []
        conditions = []

        for term, term_type, mapping in terms:
            if term_type == "column" and "column" in mapping:
                columns.append(f"- '{term}' -> column: {mapping['column']}")
            elif term_type == "logic" and "sql" in mapping:
                conditions.append(f"- '{term}' -> {mapping['sql']} ({mapping.get('description', '')})")

        if columns:
            lines.append("\n### Column Mappings")
            lines.extend(columns)

        if conditions:
            lines.append("\n### Business Logic Conditions")
            lines.extend(conditions)

        return "\n".join(lines)

    def get_required_tables(self, query: str, market: str = "KR") -> List[str]:
        """
        Get required tables based on detected terms

        Args:
            query: User query
            market: Market filter

        Returns:
            List of required table names
        """
        terms = self.extract_terms(query)
        tables = set()

        table_prefix = "kr_" if market == "KR" else "us_"

        for term, term_type, mapping in terms:
            term_tables = mapping.get("tables", [])
            for t in term_tables:
                if t.startswith(table_prefix) or t in ["market_index"]:
                    tables.add(t)

        # Add default table if none found
        if not tables:
            tables.add(f"{table_prefix}intraday" if market == "KR" else f"{table_prefix}daily")

        return list(tables)
