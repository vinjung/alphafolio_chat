# services/chat/alpha_ai_model/graph/nodes/response_generator.py
"""
Response Generation Node

Generates natural language response from:
- Query results
- User intent
- Original question context

Uses LLM for natural language generation.
Integrates with analysis_prompts.py response templates.
"""
import math
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import logger
from core.llm.factory import get_llm, LLMProvider
from ...tools.financial_calculator import FinancialCalculator
from ...tools.chart_data_formatter import chart_data_formatter
from .visualization_resolver import visualization_resolver

# Import response template utilities from analysis_prompts
from ...prompts.analysis_prompts import (
    get_template_by_intent,
    get_response_template,
    format_response_with_template,
    get_disclaimer,
    INTENT_TO_TEMPLATE_CATEGORY,
    ALL_RESPONSE_TEMPLATES,
)


# Column name translations for visualization tables (Korean)
# Complete translations from kr_SQL_table_info.csv and us_SQL_table_info.csv
COLUMN_NAME_TRANSLATIONS = {
    # ==========================================================================
    # IDENTIFIERS & BASIC INFO
    # ==========================================================================
    "symbol": "종목코드",
    "stock_name": "종목명",
    "name": "종목명",
    "ticker": "티커",
    "standard_symbol": "표준코드",
    "standard_stock_name": "표준종목명",
    "stock_name_eng": "영문종목명",
    "stock_name_kr": "한글종목명",
    "corp_code": "고유번호",
    "corp_name": "법인명",
    "corp_cls": "법인구분",
    "cik": "기업식별번호",
    "exchange": "시장구분",
    "assettype": "자산유형",
    "description": "회사설명",
    "country": "국가",
    "sector": "섹터",
    "industry": "산업",
    "industry_code": "업종코드",
    "department": "소속부",
    "securities_type": "증권구분",
    "stock_type": "주식종류",
    "stock_knd": "주식종류",
    "theme": "테마분류",
    "address": "회사주소",
    "phone": "전화번호",
    "officialSite": "공식웹사이트",
    "ceo_name": "대표이사",
    "advisor": "지정자문인",
    "aliases": "종목별칭",

    # ==========================================================================
    # PRICE DATA
    # ==========================================================================
    "close": "종가",
    "open": "시가",
    "high": "고가",
    "low": "저가",
    "price": "현재가",
    "current_price": "현재가",
    "adj_close": "수정종가",
    "change_amount": "대비",
    "change_rate": "등락률(%)",
    "change": "변동",
    "change_pct": "등락률(%)",
    "last": "최종가",
    "mark": "평가가",
    "bid": "매수호가",
    "bid_size": "매수호가수량",
    "ask": "매도호가",
    "ask_size": "매도호가수량",
    "strike": "행사가",
    "week52high": "52주최고가",
    "week52low": "52주최저가",
    "target_price": "목표가",
    "analysttargetprice": "애널리스트목표가",

    # ==========================================================================
    # VOLUME & TRADING VALUE
    # ==========================================================================
    "volume": "거래량",
    "trading_volume": "거래량",
    "trading_value": "거래대금",
    "avg_volume": "평균거래량",
    "avg_volume_5d": "거래량이평5일",
    "avg_volume_20d": "거래량이평20일",
    "avg_volume_50d": "거래량이평50일",
    "avg_volume_60d": "거래량이평60일",
    "avg_volume_200d": "거래량이평200일",
    "avg_trading_value_5d": "거래대금이평5일",
    "avg_trading_value_20d": "거래대금이평20일",
    "avg_trading_value_60d": "거래대금이평60일",
    "avg_trading_value_200d": "거래대금이평200일",
    "block_volume": "대량매매수량",
    "block_volume_rate": "대량매매비율",
    "open_interest": "미결제약정",

    # ==========================================================================
    # MARKET CAP & SHARES
    # ==========================================================================
    "market_cap": "시가총액",
    "estimated_market_cap": "시가총액",
    "listed_shares": "상장주식수",
    "sharesoutstanding": "발행주식수",
    "sharesfloat": "유통주식수",
    "common_stock_shares_outstanding": "보통주발행주식수",
    "par_value": "액면가",
    "capital": "자본금",
    "currency": "통화",
    "listed_date": "상장일",

    # ==========================================================================
    # TECHNICAL INDICATORS
    # ==========================================================================
    "rsi": "RSI",
    "macd": "MACD",
    "macd_signal": "MACD시그널",
    "macd_hist": "MACD히스토그램",
    "real_upper_band": "볼린저상단",
    "real_middle_band": "볼린저중심",
    "real_lower_band": "볼린저하단",
    "bb_upper": "볼린저상단",
    "bb_middle": "볼린저중심",
    "bb_lower": "볼린저하단",
    "vwap": "VWAP",
    "eod_vwap": "일말VWAP",
    "avg_vwap": "평균VWAP",
    "price_vs_vwap": "가격/VWAP비율",
    "atr": "ATR",
    "atr_pct": "ATR%",
    "slowk": "Stochastic%K",
    "slowd": "Stochastic%D",
    "mfi": "MFI",
    "roc": "ROC",
    "sma": "SMA",
    "ema": "EMA",
    "adx": "ADX",
    "wma": "WMA",
    "aroon": "Aroon",
    "cci": "CCI",
    "obv": "OBV",
    "ma5": "5일이평",
    "ma10": "10일이평",
    "ma20": "20일이평",
    "ma60": "60일이평",
    "ma120": "120일이평",
    "sma_20": "20일이평",
    "sma_50": "50일이평",
    "sma_200": "200일이평",
    "day50movingaverage": "50일이평",
    "day200movingaverage": "200일이평",
    "indicator": "기술적지표",
    "time_period": "기간",
    "series_type": "시리즈유형",

    # ==========================================================================
    # OPTIONS DATA
    # ==========================================================================
    "contract_id": "계약ID",
    "expiration": "만기일",
    "type": "유형",
    "implied_volatility": "내재변동성",
    "delta": "델타",
    "gamma": "감마",
    "theta": "세타",
    "vega": "베가",
    "rho": "로",
    "total_call_volume": "콜옵션거래량",
    "total_put_volume": "풋옵션거래량",
    "avg_implied_volatility": "평균내재변동성",
    "min_implied_volatility": "최소내재변동성",
    "max_implied_volatility": "최대내재변동성",
    "avg_call_iv": "콜평균IV",
    "avg_put_iv": "풋평균IV",
    "call_option_count": "콜옵션수",
    "put_option_count": "풋옵션수",
    "net_gex": "순GEX",
    "call_gex": "콜GEX",
    "put_gex": "풋GEX",
    "gex_ratio": "GEX비율",
    "gamma_flip_distance": "감마플립거리",
    "iv_percentile": "IV백분위",
    "put_call_ratio": "풋콜비율",
    "iv_skew": "IV스큐",

    # ==========================================================================
    # INVESTOR TRADING DATA
    # ==========================================================================
    "investor_type": "투자자구분",
    "category": "거래구분",
    "sell_volume": "매도량",
    "buy_volume": "매수량",
    "net_buy_volume": "순매수량",
    "sell_value": "매도대금",
    "buy_value": "매수대금",
    "net_buy_value": "순매수대금",
    "inst_buy_volume": "기관매수수량",
    "inst_sell_volume": "기관매도수량",
    "inst_net_volume": "기관순매수수량",
    "inst_buy_value": "기관매수금액",
    "inst_sell_value": "기관매도금액",
    "inst_net_value": "기관순매수금액",
    "inst_buy_ratio": "기관매수비중(%)",
    "retail_buy_volume": "개인매수수량",
    "retail_sell_volume": "개인매도수량",
    "retail_net_volume": "개인순매수수량",
    "retail_buy_value": "개인매수금액",
    "retail_sell_value": "개인매도금액",
    "retail_net_value": "개인순매수금액",
    "retail_buy_ratio": "개인매수비중(%)",
    "foreign_buy_volume": "외국인매수수량",
    "foreign_sell_volume": "외국인매도수량",
    "foreign_net_volume": "외국인순매수수량",
    "foreign_buy_value": "외국인매수금액",
    "foreign_sell_value": "외국인매도금액",
    "foreign_net_value": "외국인순매수금액",
    "foreign_buy_ratio": "외국인매수비중(%)",
    "total_buy_volume": "전체매수수량",
    "total_sell_volume": "전체매도수량",
    "total_net_volume": "전체순매수수량",
    "total_buy_value": "전체거래대금",
    "total_sell_value": "전체매도금액",
    "total_net_value": "전체순매수금액",
    "foreign_ownership": "외국인보유수량",
    "foreign_rate": "외국인지분율(%)",
    "foreign_limit": "외국인한도수량",
    "foreign_rate_limit": "외국인한도소진율(%)",
    "inst_net_30d": "기관30일순매수",
    "foreign_net_30d": "외국인30일순매수",
    "institution_net_volume": "기관순매수량",
    "institution_net_value": "기관순매수금액",
    "individual_net_volume": "개인순매수량",

    # ==========================================================================
    # FUNDAMENTALS & VALUATION
    # ==========================================================================
    "per": "PER",
    "pbr": "PBR",
    "eps": "EPS",
    "bps": "BPS",
    "roe": "ROE",
    "roa": "ROA",
    "dps": "주당배당금",
    "dividend_yield": "배당수익률(%)",
    "dividendyield": "배당수익률(%)",
    "dividendpershare": "주당배당금",
    "peg": "PEG비율",
    "bookvalue": "주당장부가치",
    "ebitda": "EBITDA",
    "ebit": "EBIT",
    "trailingpe": "후행PER",
    "forwardpe": "선행PER",
    "pricetosalesratiottm": "주가매출비율",
    "pricetobookratio": "주가장부비율",
    "evtorevenue": "EV/매출",
    "evtoebitda": "EV/EBITDA",
    "profitmargin": "이익률(%)",
    "operatingmarginttm": "영업이익률(%)",
    "returnonassetsttm": "총자산이익률(%)",
    "returnonequityttm": "자기자본이익률(%)",
    "revenuepersharettm": "주당매출",
    "revenuettm": "매출",
    "grossprofitttm": "총이익",
    "dilutedepsttm": "희석EPS",
    "quarterlyearningsgrowthyoy": "분기이익성장률(%)",
    "quarterlyrevenuegrowthyoy": "분기매출성장률(%)",
    "beta": "베타",
    "percentinsiders": "내부자지분(%)",
    "percentinstitutions": "기관보유율(%)",
    "fiscal_month": "결산월",
    "fiscalyearend": "회계연도종료월",
    "latestquarter": "최근분기",

    # ==========================================================================
    # ANALYST RATINGS
    # ==========================================================================
    "analystratingstrongbuy": "강력매수",
    "analystratingbuy": "매수",
    "analystratinghold": "보유",
    "analystratingsell": "매도",
    "analystratingstrongsell": "강력매도",
    "investment_opinion": "투자의견",
    "securities_firm": "증권사",

    # ==========================================================================
    # QUANT GRADES & SCORES
    # ==========================================================================
    "final_grade": "투자등급",
    "final_score": "최종점수",
    "total_grade": "종합등급",
    "total_score": "종합점수",
    "value_grade": "가치등급",
    "value_score": "가치점수",
    "quality_grade": "퀄리티등급",
    "quality_score": "품질점수",
    "momentum_grade": "모멘텀등급",
    "momentum_score": "모멘텀점수",
    "growth_score": "성장점수",
    "confidence_score": "신뢰도점수",
    "conviction_score": "확신도점수",
    "interaction_score": "팩터상호작용점수",
    "entry_timing_score": "진입타이밍점수",
    "value_momentum": "가치모멘텀",
    "quality_momentum": "품질모멘텀",
    "momentum_momentum": "모멘텀모멘텀",
    "growth_momentum": "성장모멘텀",
    "factor_combination_bonus": "팩터조합보너스",
    "sector_rotation_score": "섹터로테이션점수",
    "sector_momentum": "섹터모멘텀",
    "sector_rank": "섹터순위",
    "sector_percentile": "섹터백분위(%)",
    "industry_rank": "업종내순위",
    "industry_percentile": "업종내백분위(%)",
    "rs_value": "상대강도",
    "rs_rank": "상대강도등급",
    "score_trend_2w": "2주간점수변화",
    "price_position_52w": "52주가격위치(%)",

    # ==========================================================================
    # RISK METRICS
    # ==========================================================================
    "var_95": "VaR95%",
    "cvar_95": "CVaR95%",
    "volatility_annual": "연환산변동성(%)",
    "max_drawdown_1y": "1년최대낙폭(%)",
    "risk_profile_text": "리스크프로파일",
    "risk_recommendation": "투자자적합성",
    "risk_flag": "위험등급",
    "outlier_risk_score": "이상치위험점수",
    "stop_loss_pct": "손절기준(%)",
    "take_profit_pct": "익절기준(%)",
    "risk_reward_ratio": "리스크리워드비율",
    "position_size_pct": "포지션비중(%)",
    "sharpe_ratio": "샤프비율",
    "sortino_ratio": "소르티노비율",
    "calmar_ratio": "칼마비율",

    # ==========================================================================
    # SCENARIO ANALYSIS
    # ==========================================================================
    "scenario_bullish_prob": "강세확률(%)",
    "scenario_sideways_prob": "횡보확률(%)",
    "scenario_bearish_prob": "약세확률(%)",
    "scenario_bullish_return": "강세시예상수익률",
    "scenario_sideways_return": "횡보시예상수익률",
    "scenario_bearish_return": "약세시예상수익률",
    "scenario_sample_count": "시나리오샘플수",
    "buy_triggers": "매수조건",
    "sell_triggers": "매도조건",
    "hold_triggers": "보유조건",
    "time_series_text": "시계열추세",
    "signal_overall": "종합신호",
    "market_state": "시장상태",
    "strategy": "전략",

    # ==========================================================================
    # FACTOR WEIGHTS
    # ==========================================================================
    "weight_value": "가치가중치(%)",
    "weight_quality": "품질가중치(%)",
    "weight_momentum": "모멘텀가중치(%)",
    "weight_growth": "성장가중치(%)",

    # ==========================================================================
    # FINANCIAL STATEMENTS - INCOME
    # ==========================================================================
    "gross_profit": "매출총이익",
    "total_revenue": "총매출",
    "cost_of_revenue": "매출원가",
    "cost_of_goods_and_services_sold": "매출원가",
    "operating_income": "영업이익",
    "selling_general_and_administrative": "판관비",
    "research_and_development": "연구개발비",
    "operating_expenses": "영업비용",
    "investment_income_net": "순투자수익",
    "net_interest_income": "순이자수익",
    "interest_income": "이자수익",
    "interest_expense": "이자비용",
    "non_interest_income": "기타순이익",
    "other_non_operating_income": "기타비영업수익",
    "depreciation": "감가상각비",
    "depreciation_and_amortization": "감가상각및무형자산상각",
    "depreciation_depletion_and_amortization": "감가상각비등",
    "income_before_tax": "법인세차감전이익",
    "income_tax_expense": "법인세비용",
    "interest_and_debt_expense": "이자및부채비용",
    "net_income_from_continuing_operations": "계속사업순이익",
    "comprehensive_income_net_of_tax": "세후포괄손익",
    "net_income": "순이익",
    "profit_loss": "손익",

    # ==========================================================================
    # FINANCIAL STATEMENTS - BALANCE SHEET
    # ==========================================================================
    "total_assets": "자산총계",
    "total_current_assets": "유동자산",
    "cash_and_cash_equivalents_at_carrying_value": "현금및현금성자산",
    "cash_and_short_term_investments": "현금및단기투자",
    "inventory": "재고자산",
    "current_net_receivables": "유동순매출채권",
    "total_non_current_assets": "비유동자산",
    "property_plant_equipment": "유형자산",
    "accumulated_depreciation_amortization_ppe": "유형자산감가상각누계",
    "intangible_assets": "무형자산",
    "intangible_assets_excluding_goodwill": "영업권제외무형자산",
    "goodwill": "영업권",
    "investments": "투자자산",
    "long_term_investments": "장기투자자산",
    "short_term_investments": "단기투자자산",
    "other_current_assets": "기타유동자산",
    "other_non_current_assets": "기타비유동자산",
    "total_liabilities": "부채총계",
    "total_current_liabilities": "유동부채",
    "current_accounts_payable": "유동매입채무",
    "deferred_revenue": "이연수익",
    "current_debt": "유동부채중부채",
    "short_term_debt": "단기차입금",
    "total_non_current_liabilities": "비유동부채",
    "capital_lease_obligations": "자본적리스부채",
    "long_term_debt": "장기차입금",
    "current_long_term_debt": "유동성장기부채",
    "long_term_debt_noncurrent": "비유동성장기부채",
    "short_long_term_debt_total": "단기및장기부채합계",
    "other_current_liabilities": "기타유동부채",
    "other_non_current_liabilities": "기타비유동부채",
    "total_shareholder_equity": "자본총계",
    "treasury_stock": "자사주",
    "retained_earnings": "이익잉여금",
    "common_stock": "보통주자본금",

    # ==========================================================================
    # FINANCIAL STATEMENTS - CASH FLOW
    # ==========================================================================
    "operating_cashflow": "영업활동현금흐름",
    "payments_for_operating_activities": "영업활동현금지출",
    "proceeds_from_operating_activities": "영업활동현금유입",
    "change_in_operating_liabilities": "영업부채변동",
    "change_in_operating_assets": "영업자산변동",
    "capital_expenditures": "자본적지출",
    "change_in_receivables": "매출채권변동",
    "change_in_inventory": "재고자산변동",
    "cashflow_from_investment": "투자활동현금흐름",
    "cashflow_from_financing": "재무활동현금흐름",
    "proceeds_from_repayments_of_short_term_debt": "단기부채상환현금유입",
    "payments_for_repurchase_of_common_stock": "보통주재매입현금지출",
    "payments_for_repurchase_of_equity": "자본재매입현금지출",
    "payments_for_repurchase_of_preferred_stock": "우선주재매입현금지출",
    "dividend_payout": "배당금지급",
    "dividend_payout_common_stock": "보통주배당금지급",
    "dividend_payout_preferred_stock": "우선주배당금지급",
    "proceeds_from_issuance_of_common_stock": "보통주발행현금유입",
    "proceeds_from_issuance_of_long_term_debt_and_capital_securities_net": "장기부채발행현금유입",
    "proceeds_from_issuance_of_preferred_stock": "우선주발행현금유입",
    "proceeds_from_repurchase_of_equity": "자본재매입현금유입",
    "proceeds_from_sale_of_treasury_stock": "자사주매각현금유입",
    "change_in_cash_and_cash_equivalents": "현금변동",
    "change_in_exchange_rate": "환율변동",

    # ==========================================================================
    # DART FINANCIAL REPORTS (KR)
    # ==========================================================================
    "report_code": "보고서코드",
    "bsns_year": "사업연도",
    "fs_div": "개별/연결구분",
    "sj_div": "재무제표구분",
    "sj_nm": "재무제표명",
    "fs_nm": "재무제표명",
    "account_id": "계정ID",
    "account_nm": "계정명",
    "account_detail": "계정상세",
    "thstrm_nm": "당기명",
    "thstrm_amount": "당기금액",
    "thstrm_add_amount": "당기누적금액",
    "thstrm_dt": "기준일자",
    "frmtrm_nm": "전기명",
    "frmtrm_amount": "전기금액",
    "frmtrm_q_nm": "전기명(분/반기)",
    "frmtrm_q_amount": "전기금액(분/반기)",
    "frmtrm_add_amount": "전기누적금액",
    "frmtrm_dt": "기준일자",
    "bfefrmtrm_nm": "전전기명",
    "bfefrmtrm_amount": "전전기금액",
    "ord": "계정과목정렬순서",
    "rcept_no": "접수번호",
    "rcept_dt": "공시일자",
    "se": "유상증자",
    "thstrm": "당기",
    "frmtrm": "전기",
    "lwfr": "전전기",
    "stlm_dt": "결산기준일",

    # ==========================================================================
    # SHAREHOLDER & EXECUTIVE INFO (KR)
    # ==========================================================================
    "nm": "성명",
    "relate": "관계",
    "bsis_posesn_stock_co": "기초소유주식수",
    "bsis_posesn_stock_qota_rt": "기초소유주식지분율(%)",
    "trmend_posesn_stock_co": "기말소유주식수",
    "trmend_posesn_stock_qota_rt": "기말소유주식지분율(%)",
    "rm": "비고",
    "acqs_mth1": "취득방법대분류",
    "acqs_mth2": "취득방법중분류",
    "acqs_mth3": "취득방법소분류",
    "bsis_qy": "기초수량",
    "change_qy_acqs": "변동수량취득",
    "change_qy_dsps": "변동수량처분",
    "change_qy_incnr": "변동수량소각",
    "trmend_qy": "기말수량",
    "sexdstn": "성별",
    "birth_ym": "출생년월",
    "ofcps": "직위",
    "rgist_exctv_at": "등기임원여부",
    "fte_at": "상근여부",
    "chrg_job": "담당업무",
    "main_career": "주요경력",
    "mxmm_shrholdr_relate": "최대주주관계",
    "hffc_pd": "재직기간",
    "tenure_end_on": "임기만료일",

    # ==========================================================================
    # DIVIDEND & EARNINGS (US)
    # ==========================================================================
    "ex_dividend_date": "배당락일",
    "exdividenddate": "배당락일",
    "declaration_date": "배당발표일",
    "record_date": "배당권리확정일",
    "payment_date": "배당지급일",
    "dividenddate": "배당지급일",
    "amount": "금액",
    "effective_date": "효력발생일",
    "split_factor": "분할비율",
    "estimate_date": "예상날짜",
    "horizon": "예상기간",
    "eps_estimate_average": "EPS예상평균",
    "eps_estimate_high": "EPS예상최고",
    "eps_estimate_low": "EPS예상최저",
    "eps_estimate_analyst_count": "EPS예상애널리스트수",
    "revenue_estimate_average": "매출예상평균",
    "revenue_estimate_high": "매출예상최고",
    "revenue_estimate_low": "매출예상최저",
    "revenue_estimate_analyst_count": "매출예상애널리스트수",
    "reportdate": "리포트날짜",
    "fiscaldateending": "회계기간",
    "fiscal_date_ending": "회계종료일",
    "reported_currency": "보고통화",
    "estimate": "추정치",

    # ==========================================================================
    # NEWS & SENTIMENT
    # ==========================================================================
    "title": "제목",
    "url": "URL",
    "pdf_url": "PDF URL",
    "time_published": "발행시간",
    "authors": "기자",
    "summary": "요약",
    "banner_image": "배너이미지",
    "source": "출처",
    "category_within_source": "카테고리",
    "source_domain": "출처도메인",
    "topics": "주제",
    "relevance_score": "관련성점수",
    "overall_sentiment_score": "전체감정점수",
    "overall_sentiment_label": "전체감정레이블",
    "symbol_sentiment": "종목감정",
    "relevance_score_t": "관련성점수T",
    "ticker_sentiment_score": "티커감정점수",
    "ticker_sentiment_label": "티커감정레이블",

    # ==========================================================================
    # INSIDER TRADING (US)
    # ==========================================================================
    "executive": "내부거래자",
    "executive_title": "직책",
    "security_type": "증권종류",
    "acquisition_or_disposal": "매수/매도",
    "shares": "주식수량",
    "share_price": "주당가격",
    "insider_signal": "내부자거래신호",

    # ==========================================================================
    # MARKET REGIME & MACRO (US)
    # ==========================================================================
    "regime": "레짐",
    "vix_proxy": "VIX대리",
    "spy_return_1m": "SPY1개월수익률",
    "spy_return_3m": "SPY3개월수익률",
    "spy_ma200_distance": "SPYMA200거리",
    "nasdaq_vs_spy_3m": "나스닥vsSPY3개월",
    "fed_rate": "연준금리",
    "fed_rate_change_6m": "연준금리6개월변화",
    "cpi_yoy": "CPI전년비(%)",
    "unemployment_rate": "실업률(%)",
    "value": "값",
    "unit": "단위",
    "interval": "데이터간격",

    # ==========================================================================
    # SECTOR BENCHMARKS (US)
    # ==========================================================================
    "pe_p25": "PER25분위",
    "pe_median": "PER중앙값",
    "pe_p75": "PER75분위",
    "forward_pe_median": "선행PER중앙값",
    "peg_median": "PEG중앙값",
    "ps_median": "PSR중앙값",
    "ev_ebitda_median": "EV/EBITDA중앙값",
    "gross_margin_p25": "매출총이익률25분위",
    "gross_margin_median": "매출총이익률중앙값",
    "gross_margin_p75": "매출총이익률75분위",
    "operating_margin_median": "영업이익률중앙값",
    "roic_median": "ROIC중앙값",
    "roe_median": "ROE중앙값",
    "revenue_growth_median": "매출성장률중앙값",
    "eps_growth_median": "EPS성장률중앙값",
    "return_1m_median": "1개월수익률중앙값",
    "return_3m_median": "3개월수익률중앙값",
    "return_6m_median": "6개월수익률중앙값",

    # ==========================================================================
    # ECONOMIC INDICATORS
    # ==========================================================================
    "stat_code": "통계코드",
    "stat_name": "통계명",
    "item_code1": "항목코드1",
    "item_name1": "항목명1",
    "item_code2": "항목코드2",
    "item_name2": "항목명2",
    "item_code3": "항목코드3",
    "item_name3": "항목명3",
    "item_code4": "항목코드4",
    "item_name4": "항목명4",
    "unit_name": "단위명",
    "wgt": "가중치",
    "cycle": "주기",
    "time_value": "시간값",
    "time_original": "원래시간",
    "data_value": "데이터값",

    # ==========================================================================
    # MARKET INDEX
    # ==========================================================================
    "index_name": "지수명",
    "index_category": "지수분류",
    "sector_code": "섹터코드",
    "avg_return_30d": "30일평균수익률(%)",
    "stock_count": "종목수",

    # ==========================================================================
    # IPO
    # ==========================================================================
    "ipodate": "상장날짜",
    "priceRangeLow": "상장예상금액최소",
    "priceRangeHigh": "상장예상금액최대",

    # ==========================================================================
    # RESEARCH REPORTS
    # ==========================================================================
    "report_id": "리포트ID",

    # ==========================================================================
    # DATES & TIMESTAMPS
    # ==========================================================================
    "date": "날짜",
    "trade_date": "거래일",
    "created_at": "생성일시",
    "updated_at": "수정일시",
    "last_refreshed": "최신갱신일",
    "time_zone": "시간대",

    # ==========================================================================
    # INVESTMENT STRATEGY / SCENARIO
    # ==========================================================================
    "final_grade": "퀀트등급",
    "final_score": "종합점수",
    "scenario_bullish_prob": "상승확률(%)",
    "scenario_sideways_prob": "횡보확률(%)",
    "scenario_bearish_prob": "하락확률(%)",
    "scenario_bullish_return": "상승시수익률",
    "scenario_sideways_return": "횡보시수익률",
    "scenario_bearish_return": "하락시수익률",
    "stop_loss_pct": "손절가(%)",
    "take_profit_pct": "목표가(%)",
    "risk_reward_ratio": "리스크리워드비율",
    "entry_timing_score": "진입타이밍점수",
    "position_size_pct": "포지션비중(%)",
    "buy_triggers": "매수트리거",
    "sell_triggers": "매도트리거",
    "hold_triggers": "관망트리거",
    "signal_overall": "종합신호",
    "market_state": "시장상태",
    "risk_profile_text": "리스크프로파일",
    "risk_recommendation": "리스크권고",

    # ==========================================================================
    # MISC
    # ==========================================================================
    "rank": "순위",
    "ranking": "순위",
    "id": "ID",
}

# Word-level translations for decomposing LLM-generated SQL aliases
# Used when a column name is not found in COLUMN_NAME_TRANSLATIONS
COLUMN_WORD_TRANSLATIONS = {
    # Aggregations
    "cumul": "누적", "cum": "누적", "total": "합계", "sum": "합계",
    "avg": "평균", "mean": "평균", "cnt": "건수", "count": "건수",
    "min": "최소", "max": "최대",
    # Investor types
    "foreign": "외국인", "inst": "기관", "institutional": "기관",
    "retail": "개인", "individual": "개인",
    # Trading
    "net": "순매수", "buy": "매수", "sell": "매도",
    "volume": "거래량", "value": "거래대금", "amount": "금액",
    # Price
    "price": "가격", "close": "종가", "open": "시가", "high": "고가", "low": "저가",
    "change": "변동", "rate": "률", "ratio": "비율", "pct": "%",
    # Time
    "date": "일자", "latest": "최근", "first": "최초", "last": "최종",
    "days": "일수", "period": "기간", "after": "이후", "before": "이전",
    # Technical
    "breakout": "돌파", "cross": "교차", "signal": "시그널",
    "surge": "급증", "increase": "증가", "decrease": "감소",
    "sma": "이동평균", "ema": "지수이동평균", "rsi": "RSI", "macd": "MACD",
    # Performance
    "gain": "수익률", "profit": "수익", "loss": "손실", "return": "수익률",
    "rank": "순위", "score": "점수", "grade": "등급",
    # Identifiers
    "name": "종목명", "stock": "종목", "symbol": "코드",
    "market": "시장", "cap": "시가총액", "sector": "업종",
    "trading": "거래", "current": "현재",
}


def translate_column_name(col: str) -> str:
    """
    Translate column name to Korean.
    Handles both known DB columns and LLM-generated SQL aliases.

    Strategy:
    1. Direct lookup in COLUMN_NAME_TRANSLATIONS (exact match)
    2. Decompose underscore-separated alias and translate known parts
    3. Single word lookup in COLUMN_WORD_TRANSLATIONS
    4. Return original if no translation found
    """
    # 1. Direct lookup (exact match)
    if col in COLUMN_NAME_TRANSLATIONS:
        return COLUMN_NAME_TRANSLATIONS[col]
    col_lower = col.lower()
    if col_lower in COLUMN_NAME_TRANSLATIONS:
        return COLUMN_NAME_TRANSLATIONS[col_lower]

    # 2. Decompose by underscore and translate parts
    parts = col_lower.replace("-", "_").split("_")
    if len(parts) > 1:
        translated = [COLUMN_WORD_TRANSLATIONS.get(p, p) for p in parts]
        if translated != parts:
            return " ".join(translated)

    # 3. Single word lookup
    if col_lower in COLUMN_WORD_TRANSLATIONS:
        return COLUMN_WORD_TRANSLATIONS[col_lower]

    # 4. Return original
    return col


def calculate_financial_metrics(results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Calculate financial metrics from query results if price/volume data exists.

    Args:
        results: Query result list

    Returns:
        Dictionary with calculated metrics, or None if no calculable data
    """
    if not results or len(results) < 2:
        return None

    try:
        # Try to extract price data (look for common column names)
        price_columns = ["close", "price", "current_price", "adj_close"]
        volume_columns = ["volume", "trading_volume"]
        date_columns = ["date", "trade_date", "datetime", "timestamp"]

        prices = []
        volumes = []

        # Find which columns exist
        sample_row = results[0]
        price_col = None
        volume_col = None
        date_col = None

        for col in price_columns:
            if col in sample_row:
                price_col = col
                break

        for col in volume_columns:
            if col in sample_row:
                volume_col = col
                break

        for col in date_columns:
            if col in sample_row:
                date_col = col
                break

        # Data already sorted ASC by sql_executor
        sorted_results = results

        # Extract data if price column found (from sorted results)
        if price_col:
            for row in sorted_results:
                val = row.get(price_col)
                if val is not None:
                    try:
                        prices.append(float(val))
                    except (ValueError, TypeError):
                        pass

        if volume_col:
            for row in sorted_results:
                val = row.get(volume_col)
                if val is not None:
                    try:
                        volumes.append(int(val))
                    except (ValueError, TypeError):
                        pass

        # Calculate metrics if we have enough price data
        if len(prices) >= 2:
            metrics = {}

            # Basic return
            total_return = FinancialCalculator.calculate_total_return(prices)
            if total_return is not None:
                metrics["total_return"] = f"{total_return:+.2f}%"

            # If we have enough data for advanced metrics
            if len(prices) >= 5:
                volatility = FinancialCalculator.calculate_volatility(prices)
                if volatility is not None:
                    metrics["volatility"] = f"{volatility:.2f}%"

                max_dd = FinancialCalculator.calculate_max_drawdown(prices)
                if max_dd is not None:
                    metrics["max_drawdown"] = f"{max_dd:.2f}%"

            # Price statistics
            metrics["high"] = FinancialCalculator.format_number(max(prices), 0)
            metrics["low"] = FinancialCalculator.format_number(min(prices), 0)
            metrics["start_price"] = FinancialCalculator.format_number(prices[0], 0)
            metrics["end_price"] = FinancialCalculator.format_number(prices[-1], 0)

            # Volume metrics if available
            if len(volumes) >= 2:
                avg_vol = FinancialCalculator.calculate_average_volume(volumes)
                if avg_vol:
                    metrics["avg_volume"] = FinancialCalculator.format_number(avg_vol, 0)

            if metrics:
                logger.info(
                    f"[ResponseGenerator] Calculated metrics: {list(metrics.keys())} | "
                    f"prices[0:3]={prices[:3]}, prices[-3:]={prices[-3:]}, "
                    f"total_return={metrics.get('total_return')}, "
                    f"volatility={metrics.get('volatility')}, "
                    f"max_drawdown={metrics.get('max_drawdown')}"
                )
                return metrics

        return None

    except Exception as e:
        logger.warning(f"[ResponseGenerator] Metrics calculation failed: {e}")
        return None


def format_metrics_for_prompt(metrics: Optional[Dict[str, Any]], market: str = "KR") -> str:
    """
    Format calculated metrics for inclusion in LLM prompt with benchmark context.

    Args:
        metrics: Dictionary of calculated metrics
        market: Market type (KR/US) for benchmark references

    Returns:
        Formatted string for prompt with contextual benchmarks
    """
    if not metrics:
        return "No additional metrics calculated."

    lines = []
    metric_labels = {
        "total_return": "Total Return",
        "volatility": "Volatility (Annualized)",
        "max_drawdown": "Max Drawdown (MDD)",
        "sharpe_ratio": "Sharpe Ratio",
        "high": "Period High",
        "low": "Period Low",
        "start_price": "Start Price",
        "end_price": "End Price",
        "avg_volume": "Average Volume",
    }

    # Benchmark context per metric and market
    if market == "US":
        benchmark_context = {
            "volatility": "(Ref: S&P 500 avg ~15%, NASDAQ avg ~20-25%)",
            "max_drawdown": "(Ref: normal -5%~-10%, correction -10%~-20%, bear -20%~-35%)",
            "total_return": "(Compare to S&P 500 return for same period to assess alpha)",
        }
    else:
        benchmark_context = {
            "volatility": "(Ref: KOSPI avg ~15-20%, KOSDAQ avg ~25-35%)",
            "max_drawdown": "(Ref: normal -5%~-15%, correction -15%~-25%, bear -25%~-40%)",
            "total_return": "(Compare to KOSPI/KOSDAQ return for same period to assess alpha)",
        }

    for key, value in metrics.items():
        label = metric_labels.get(key, key)
        context = benchmark_context.get(key, "")
        if context:
            lines.append(f"- {label}: {value} {context}")
        else:
            lines.append(f"- {label}: {value}")

    return "\n".join(lines)


# =============================================================================
# EXPLAINABILITY UTILITIES
# =============================================================================

def build_data_source_section(state: Dict[str, Any]) -> str:
    """
    Build data source explanation section from state.

    Args:
        state: Graph state containing processing info

    Returns:
        Formatted string with data sources used
    """
    if not state:
        return "No data source information available."

    lines = ["### Data Sources Used"]

    # SQL/Database sources
    generated_sql = state.get("generated_sql", "")
    if generated_sql:
        # Extract table names from SQL
        tables = _extract_tables_from_sql(generated_sql)
        if tables:
            lines.append(f"- **Database Tables**: {', '.join(tables)}")

        # Add query info
        result_count = state.get("result_count", 0)
        if result_count:
            lines.append(f"- **Query Results**: {result_count} rows retrieved")

    # External API sources
    news_data = state.get("news_data", [])
    if news_data:
        lines.append(f"- **News API**: {len(news_data)} articles fetched")

    news_sentiment = state.get("news_sentiment")
    if news_sentiment:
        overall = news_sentiment.get("overall", "NEUTRAL")
        pos = news_sentiment.get("positive_count", 0)
        neg = news_sentiment.get("negative_count", 0)
        neu = news_sentiment.get("neutral_count", 0)
        lines.append(f"- **Sentiment Analysis**: {overall} (Pos:{pos}/Neg:{neg}/Neu:{neu})")

    disclosure_data = state.get("disclosure_data", [])
    if disclosure_data:
        lines.append(f"- **DART Disclosures**: {len(disclosure_data)} items")

    # Schema/RAG sources
    relevant_tables = state.get("relevant_tables", [])
    if relevant_tables:
        lines.append(f"- **RAG Retrieved Tables**: {len(relevant_tables)} relevant tables")

    few_shot_examples = state.get("few_shot_examples", [])
    if few_shot_examples:
        lines.append(f"- **Similar Examples**: {len(few_shot_examples)} reference queries")

    # Timestamp (KST for Korean market hours)
    from datetime import datetime, timezone, timedelta
    KST = timezone(timedelta(hours=9))
    lines.append(f"- **Analysis Time**: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")

    if len(lines) == 1:
        return "No specific data sources tracked."

    return "\n".join(lines)


def _extract_tables_from_sql(sql: str) -> List[str]:
    """
    Extract table names from SQL query.

    Args:
        sql: SQL query string

    Returns:
        List of table names
    """
    import re

    tables = set()

    # FROM clause
    from_matches = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
    tables.update(from_matches)

    # JOIN clause
    join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
    tables.update(join_matches)

    # CTE (WITH clause)
    # Exclude CTE names, only keep actual table references
    cte_names = set(re.findall(r'WITH\s+(\w+)\s+AS', sql, re.IGNORECASE))
    tables = tables - cte_names

    return sorted(list(tables))


def build_reasoning_section(state: Dict[str, Any]) -> str:
    """
    Build reasoning explanation based on data used.

    Args:
        state: Graph state

    Returns:
        Formatted reasoning hints for LLM
    """
    if not state:
        return ""

    lines = ["### Reasoning Hints (For LLM reference)"]

    intent = state.get("intent", "query")
    lines.append(f"- Query Intent: {intent}")

    # Add intent-specific reasoning hints
    reasoning_hints = {
        "ranking": "Compare values and explain why top items stand out",
        "technical": "Interpret indicator values against standard thresholds",
        "filter": "Explain what conditions were met",
        "investor": "Analyze supply-demand implications",
        "quant": "Explain factor scores and their investment meaning",
        "market": "Provide market context and trend analysis",
        "query": "Present data clearly with relevant context"
    }

    hint = reasoning_hints.get(intent, "Provide clear analysis with data support")
    lines.append(f"- Analysis Focus: {hint}")

    # Entities for context
    entities = state.get("entities", {})
    if entities:
        stock_names = entities.get("stock_names", [])
        if stock_names:
            lines.append(f"- Target Stocks: {', '.join(stock_names)}")

        indicators = entities.get("indicators", [])
        if indicators:
            lines.append(f"- Indicators Mentioned: {', '.join(indicators)}")

    return "\n".join(lines)


def calculate_confidence_level(state: Dict[str, Any]) -> Dict[str, str]:
    """
    Calculate overall confidence level based on data completeness.

    Args:
        state: Graph state

    Returns:
        Dict with level and reasons
    """
    if not state:
        return {"level": "LOW", "reason": "Insufficient data"}

    score = 0
    factors = []

    # Check data completeness
    if state.get("query_result"):
        result_count = state.get("result_count", 0)
        if result_count > 0:
            score += 30
            factors.append("DB data available")
        if result_count >= 10:
            score += 10
            factors.append("Sufficient sample size")

    if state.get("news_data"):
        score += 15
        factors.append("News data included")

    news_sentiment = state.get("news_sentiment")
    if news_sentiment:
        confidence = news_sentiment.get("confidence", "LOW")
        if confidence == "HIGH":
            score += 15
            factors.append("High sentiment confidence")
        elif confidence == "MEDIUM":
            score += 10
            factors.append("Moderate sentiment confidence")

    if state.get("disclosure_data"):
        score += 10
        factors.append("Disclosure data included")

    if state.get("few_shot_examples"):
        score += 10
        factors.append("Similar query examples found")

    if not state.get("sql_error"):
        score += 10
        factors.append("No query errors")

    # Determine level
    if score >= 60:
        level = "HIGH"
    elif score >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    level_kr = {"HIGH": "높음", "MEDIUM": "중간", "LOW": "낮음"}

    return {
        "level": level,
        "level_kr": level_kr.get(level, level),
        "score": score,
        "factors": factors,
        "formatted": f"**Confidence Level**: {level_kr.get(level, level)} ({', '.join(factors[:3])})"
    }


def format_explainability_for_prompt(state: Dict[str, Any]) -> str:
    """
    Format complete explainability section for LLM prompt.

    Args:
        state: Graph state

    Returns:
        Combined explainability information
    """
    sections = []

    # Data sources
    data_sources = build_data_source_section(state)
    if data_sources:
        sections.append(data_sources)

    # Reasoning hints
    reasoning = build_reasoning_section(state)
    if reasoning:
        sections.append(reasoning)

    # Confidence
    confidence = calculate_confidence_level(state)
    sections.append(confidence.get("formatted", ""))

    return "\n\n".join(sections)


# Response generation prompt with template guidance and explainability
RESPONSE_GENERATION_PROMPT = """You are Alpha AI, a professional financial data analyst.
Based on the query results below, provide a clear and informative response in Korean.

## User Question
{question}

## Query Results
{results}

## Calculated Metrics (Pre-calculated - use these exact values, do not recalculate)
{calculated_metrics}

## Data Sources & Analysis Context
{explainability_info}

## Supplementary Analysis Context (Additional data automatically retrieved for deeper analysis)
{supplementary_context}

## Response Template (Follow this structure)
{response_template}

## Response Guidelines
1. Follow the template structure above
2. Fill in actual data from query results
3. Use the pre-calculated metrics above for any return/volatility/drawdown values
4. Present numbers with proper formatting (commas for thousands)
5. Provide professional interpretation and insights
6. Be concise - maximum 3 top-level sections
7. Do not use emojis
8. Include disclaimer if dealing with investment-related content
9. Use Supplementary Analysis Context to provide comparative analysis:
   - Compare stock metrics with sector/industry averages (e.g., "RSI 28.5, industry avg 55.8")
   - Reference indicator trends (e.g., "RSI dropped 15pt over 5 days")
   - Include investor flow patterns when available (e.g., "Foreign investors net buying for 3 consecutive days")
   - Mention market context when relevant
   - ONLY reference supplementary data that is actually provided - do not fabricate comparisons
10. Focus your analysis on data from Query Results and Additional Query Results above.
   - Available columns: {available_columns}
   - If primary Query Results are empty but Additional Query Results have data, analyze that data
   - Do NOT fabricate numerical values not present in any of the results
   - If specific data the user asked for is genuinely not in any results, state which data is missing
   - NEVER say "데이터가 제한적입니다" when data IS provided in Query Results or Additional Query Results
   - Only claim "데이터 없음" when the section is genuinely empty
11. When the Response Template starts with a headline conclusion format (e.g., "핵심 결론"),
    you MUST begin your response with that headline using the actual investment grade data
    from the Supplementary Analysis Context's "투자 등급" section.
    The first line must show the final_grade value prominently.
    If stock grade data is not available in supplementary context, skip the headline
    and proceed with the rest of the analysis.

## CRITICAL: Numbered List Hierarchy Rules
When writing numbered sections with sub-items, use DISTINCT formats for each level:
- Top-level sections: Use "1." "2." "3." format
- Sub-items under a section: Use "1)" "2)" "3)" format
- Third-level items (if any): Use bullet points "-"

Example of CORRECT hierarchy:
1. Main Section Title
분석 내용...
1) First sub-point
2) Second sub-point
3) Third sub-point

2. Another Main Section
1) Sub-point A
2) Sub-point B

Example of WRONG hierarchy (DO NOT do this):
1. Main Section Title
1. First sub-point  (WRONG - same format as parent)
2. Second sub-point

## CRITICAL: Data Analysis Guidelines
1. **Data Direction Check**:
   - ALWAYS verify price direction from actual data before stating "상승" or "하락"
   - Check the "Total Return" value in Calculated Metrics section
   - If total_return is POSITIVE (+), the stock ROSE during the period
   - If total_return is NEGATIVE (-), the stock FELL during the period
   - NEVER contradict the calculated metrics with your analysis

2. **News-Data Cross Validation**:
   - Compare news sentiment with actual price movement from data
   - If sentiment is POSITIVE but total_return is negative, explicitly mention this divergence
   - If sentiment is NEGATIVE but total_return is positive, explicitly mention this divergence
   - Example: "뉴스 감성은 긍정적이나 실제 주가는 X% 하락하여 괴리가 발생했습니다"

3. **Metric Consistency**:
   - Use ONLY the pre-calculated metrics provided in "Calculated Metrics" section
   - Do NOT recalculate returns, volatility, or drawdown yourself
   - Quote the exact values (e.g., "분석 기간 수익률 +15.5%")

## Financial Metric Interpretation Rules (MUST follow)
When interpreting financial metrics, ALWAYS provide contextual comparison. Raw numbers alone are meaningless.

1. **Volatility**: NEVER state "변동성이 높다/낮다" without benchmark comparison.
   - KR: KOSPI avg ~15-20%, KOSDAQ avg ~25-35%
   - US: S&P 500 avg ~15%, NASDAQ avg ~20-25%
   - Ranges: <15% low (defensive), 15-25% moderate (large-cap), 25-40% high (growth), >40% very high (speculative)
   - ALWAYS consider sector characteristics (e.g., tech/biotech typically higher than utilities)
   - GOOD example: "변동성 24.5%로 코스피 평균(18%) 대비 약 6.5%p 높으나, 반도체 업종 평균(28%) 대비 양호한 수준"
   - BAD example: "변동성 24.5%로 리스크가 높습니다"

2. **MDD (Max Drawdown)**: ALWAYS compare to market condition for the same period.
   - Normal market: -5% to -15%
   - Market correction: -15% to -25%
   - Bear market: -25% to -40%
   - Crisis: worse than -40%
   - GOOD example: "MDD -12.3%로 같은 기간 코스피(-8.5%) 대비 다소 큰 낙폭이나, 정상 범위(-5%~-15%) 내 위치"
   - BAD example: "MDD -12.3%로 손실 위험이 큽니다"

3. **Total Return**: Compare to benchmark index return for the same period.
   - If outperformed: mention alpha (excess return)
   - If underperformed: mention the gap and possible reasons
   - Annualize returns for periods longer than 1 year

4. **General Rule**: Provide specific comparative numbers (e.g., "X%p above/below benchmark"), not vague qualitative statements.

## CRITICAL: Data Table Display Rules
The data table is displayed SEPARATELY by the frontend visualization component.
DO NOT create duplicate data displays in your response.

MUST INCLUDE (at the beginning):
- Analysis metadata: date/time, market (e.g., "분석 기준: 2026-01-10 | 시장: 한국거래소")
- Target stocks list (e.g., "대상 종목: 삼성전자, SK하이닉스, 삼성바이오로직스")

DO NOT INCLUDE:
- Markdown tables (|---|---| format) - FORBIDDEN
- Row-by-row data listing (e.g., "삼성전자: 시가총액 8,228,297억, 종가 139,000원, 점수 58.3점...")
- Repeating the same numbers that appear in the data table

FOCUS ON:
- Analysis and interpretation of the data
- Investment insights and recommendations
- Key patterns, comparisons, and observations
- Risk factors and opportunities
- You MAY reference specific numbers naturally within analysis sentences
  (e.g., "모멘텀 점수가 24점으로 낮아 단기 상승 동력이 부족합니다")

## Important Constraints (Investment Advisory)
- NEVER use absolute predictions (e.g., "무조건 오릅니다", "반드시 떨어집니다", "확실히 상승합니다" - FORBIDDEN)
- ALWAYS mention potential risks when discussing investment opportunities
- ALWAYS include the legal disclaimer at the end for investment-related content
- Prohibited keywords (ABSOLUTE BAN): 추천, 권유, 확정, 확실, 무조건, 반드시, 틀림없이, 보장
- Do NOT use: "~을 추천합니다", "매수/매도를 권유", "확실히 ~합니다"
- Instead use: "~할 가능성이 있습니다", "~를 고려해 볼 수 있습니다", "~로 판단됩니다"

## IMPORTANT: Response Ending Requirements
At the end of your response, include in this EXACT order:

1. [추론 근거] section:
---
[추론 근거]
- Explain key data points that led to your conclusions
- Reference specific values and thresholds

2. Then ALWAYS end with this disclaimer as the FINAL lines:
---
※ 본 서비스 및 LLM이 제공하는 모든 정보, 분석, 예측, 의견 등은 일반적인 참고용 정보이며, 「자본시장과 금융투자업에 관한 법률」상 투자자문 또는 투자권유에 해당하지 않습니다.
※ 본 서비스는 이용자의 투자 목적, 재산 상황, 투자 경험 등을 고려하지 않으며, 제공되는 정보의 정확성, 완전성, 최신성을 보장하지 않습니다.
※ 과거 데이터나 모형에 기반한 설명 및 예시는 미래 수익률이나 성과를 보장하지 않습니다.
※ 투자에 대한 최종 판단과 그에 따른 손실 및 법적 책임은 전적으로 이용자 본인에게 있으며, 본 서비스 제공자 및 개발자는 이에 대해 어떠한 책임도 지지 않습니다.

DO NOT include [데이터 출처] or [확실성] sections.
The disclaimer MUST be the absolute last lines of your response.

Respond in Korean:"""


def format_table_response(results: List[Dict[str, Any]], limit: int = 20) -> str:
    """
    Format query results as markdown table

    Args:
        results: List of result dictionaries
        limit: Maximum rows to display

    Returns:
        Markdown formatted table string
    """
    if not results:
        return "No results found."

    # Get columns from first result
    columns = list(results[0].keys())

    # Build header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    # Build rows
    rows = []
    for row in results[:limit]:
        values = []
        for col in columns:
            val = row.get(col, "")
            # Format numbers
            if isinstance(val, float):
                if abs(val) >= 1000000000000:  # Trillion
                    val = f"{val/1000000000000:,.1f}T"
                elif abs(val) >= 100000000:  # 100 million
                    val = f"{val/100000000:,.1f}B"
                elif abs(val) >= 1000000:  # Million
                    val = f"{val/1000000:,.1f}M"
                else:
                    val = f"{val:,.2f}"
            elif isinstance(val, int):
                if abs(val) >= 1000000000000:
                    val = f"{val/1000000000000:,.1f}T"
                elif abs(val) >= 100000000:
                    val = f"{val/100000000:,.1f}B"
                elif abs(val) >= 1000000:
                    val = f"{val/1000000:,.1f}M"
                else:
                    val = f"{val:,}"
            else:
                val = str(val) if val is not None else "-"
            values.append(val)
        rows.append("| " + " | ".join(values) + " |")

    table = "\n".join([header, separator] + rows)

    if len(results) > limit:
        table += f"\n\n... and {len(results) - limit} more rows"

    return table


def fix_numbering_hierarchy(text: str) -> str:
    """Fix numbering hierarchy: top-level uses 'N.', sub-items use 'N)'.

    Handles four problems:
    1. Lazy '1. 1. 1.' repetition -> sequential '1. 2. 3.'
    2. Indented 'N.' (same format as parent) -> 'N)' for child items
    3. 'N)' at indent 0 after top-level 'N.' -> add 3-space indent for markdown nesting
    4. Dash bullets '- ' after top-level 'N.' -> convert to 'N)' with indent
    """
    import re
    if not text:
        return text

    lines = text.split('\n')
    top_counter = 0
    sub_counter = 0
    has_top_section = False
    fixed_lines = []
    for line in lines:
        stripped = line.lstrip()
        indent_len = len(line) - len(stripped)

        # Dash bullet after a top-level N. section -> convert to N) with indent
        if re.match(r'^- ', stripped) and has_top_section:
            sub_counter += 1
            content = stripped[2:]
            fixed_lines.append(f"   {sub_counter}) {content}")
            continue

        # N) at indent 0 after a top-level N. section -> indent for nesting
        if indent_len == 0 and re.match(r'^\d+\)\s', stripped) and has_top_section:
            num_match = re.match(r'^(\d+)\)\s(.*)', stripped)
            if num_match:
                num = int(num_match.group(1))
                content = num_match.group(2)
                if num == 1:
                    sub_counter = 1
                else:
                    sub_counter = num
                fixed_lines.append(f"   {sub_counter}) {content}")
            else:
                fixed_lines.append(line)

        # Sub-items with "N)" format already indented -> normalize to 3-space indent
        elif indent_len > 0 and re.match(r'^1\)\s', stripped):
            sub_counter += 1
            fixed_lines.append(f"   {sub_counter}) {stripped[3:]}")
        elif indent_len > 0 and re.match(r'^[2-9]\)\s|^\d{2,}\)\s', stripped):
            num_match = re.match(r'^(\d+)\)\s', stripped)
            if num_match:
                sub_counter = int(num_match.group(1))
            fixed_lines.append(f"   {stripped}")

        # Sub-items with "N." format (WRONG hierarchy - convert to "N)")
        elif indent_len > 0 and re.match(r'^\d+\.\s', stripped):
            num_match = re.match(r'^(\d+)\.\s(.*)', stripped)
            if num_match:
                num = int(num_match.group(1))
                content = num_match.group(2)
                if num == 1:
                    sub_counter += 1
                    fixed_lines.append(f"   {sub_counter}) {content}")
                else:
                    fixed_lines.append(f"   {num}) {content}")
            else:
                fixed_lines.append(line)

        # Top-level items with "1." format (fix lazy repetition)
        elif indent_len == 0 and re.match(r'^1\.\s', stripped):
            top_counter += 1
            sub_counter = 0
            has_top_section = True
            fixed_lines.append(f"{top_counter}. {stripped[3:]}")
        elif re.match(r'^[2-9]\.\s|^\d{2,}\.\s', stripped):
            if indent_len == 0:
                sub_counter = 0
                top_counter = 0
                has_top_section = True
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    # Second pass: merge N) lines with no content into the next non-empty line
    merged_lines = []
    i = 0
    while i < len(fixed_lines):
        line = fixed_lines[i]
        stripped = line.rstrip()
        # Check if line is just "N)" with no content (e.g., "   1) " or "1)")
        if re.match(r'^\s*\d+\)\s*$', stripped):
            # Look ahead for next non-empty line to merge
            j = i + 1
            while j < len(fixed_lines) and fixed_lines[j].strip() == '':
                j += 1
            if j < len(fixed_lines):
                next_content = fixed_lines[j].strip()
                indent = line[:len(line) - len(line.lstrip())]
                num_match = re.match(r'^(\s*\d+\))\s*$', stripped)
                if num_match:
                    merged_lines.append(f"{num_match.group(1)} {next_content}")
                    i = j + 1
                    continue
        merged_lines.append(line)
        i += 1

    return '\n'.join(merged_lines)


def remove_markdown_formatting(text: str) -> str:
    """
    Remove all markdown formatting from text when visualization is provided.

    Removes:
    - Markdown tables
    - Headers (# ## ### etc.)
    - Bold/italic formatting
    - Inline code

    Args:
        text: Response text that may contain markdown formatting

    Returns:
        Text with markdown formatting removed
    """
    import re

    if not text:
        return text

    result = text

    # 1. Remove markdown tables
    # Pattern 1: Standard markdown tables with separator row
    table_pattern_1 = r'\|[^\n]+\|\s*\n\|[-:\s|]+\|\s*\n(?:\|[^\n]+\|\s*\n?)+'
    # Pattern 2: Tables without proper separator (just pipe-delimited rows)
    table_pattern_2 = r'(?:^\|[^\n]+\|\s*$\n?){3,}'
    result = re.sub(table_pattern_1, '', result, flags=re.MULTILINE)
    result = re.sub(table_pattern_2, '', result, flags=re.MULTILINE)

    # 2. Remove headers (# ## ### etc.)
    result = re.sub(r'^#{1,6}\s+', '', result, flags=re.MULTILINE)

    # 3. Remove bold/italic (**text**, *text*, __text__, _text_)
    result = re.sub(r'\*\*([^*]+)\*\*', r'\1', result)
    result = re.sub(r'\*([^*]+)\*', r'\1', result)
    result = re.sub(r'__([^_]+)__', r'\1', result)
    result = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'\1', result)

    # 4. Remove inline code (`code`)
    result = re.sub(r'`([^`]+)`', r'\1', result)

    # 5. Fix repeated "1." markdown numbering with hierarchy awareness
    result = fix_numbering_hierarchy(result)

    # 6. Remove "... and X more rows" messages that follow tables
    result = re.sub(r'\.\.\. and \d+ more rows?\s*\n?', '', result)

    # 7. Remove standalone "Total: X rows" lines
    result = re.sub(r'\n?Total:\s*\d+\s*rows?\s*\n?', '\n', result, flags=re.IGNORECASE)

    # 8. Clean up extra blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = re.sub(r'\n\s+\n', '\n\n', result)

    return result.strip()


def _generate_visualization_title(
    message: str,
    intent: str,
    result_count: int,
    sub_query_question: str = "",
) -> str:
    """
    Generate visualization title based on actual query results.

    Priority: sub_query_question (actual SQL query description) > message keywords.
    This ensures the title matches the actual table/chart data.

    Args:
        message: User's original question
        intent: Detected intent
        result_count: Number of rows in result
        sub_query_question: Primary sub-query question describing the actual data

    Returns:
        Title string for visualization
    """
    # Priority 1: Use sub-query question (describes actual data content)
    if sub_query_question:
        title = sub_query_question
        # Remove screening/CTE prefixes
        if "[SCREENING QUERY" in title:
            bracket_end = title.find("] ")
            if bracket_end != -1:
                title = title[bracket_end + 2:]
        # Remove CTE suffixes
        for suffix in ["를 CTE로 조회", "을 CTE로 조회", "CTE로 조회"]:
            if title.endswith(suffix):
                title = title[:-len(suffix)].rstrip()
                break
        # Truncate if too long
        if len(title) > 60:
            title = title[:57] + "..."
        return f"{title} ({result_count}개)"

    # Priority 2: Rule-based matching for simple queries
    intent_titles = {
        "ranking": "순위 조회 결과",
        "filter": "조건 검색 결과",
        "technical": "기술적 지표 분석",
        "investor": "투자자 동향",
        "quant": "퀀트 분석 결과",
        "market": "시장 지표",
        "macro": "매크로 지표",
        "query": "조회 결과"
    }

    if "상위" in message or "순위" in message or "랭킹" in message:
        if "거래대금" in message:
            return f"거래대금 상위 {result_count}개 종목"
        elif "거래량" in message:
            return f"거래량 상위 {result_count}개 종목"
        elif "시가총액" in message or "시총" in message:
            return f"시가총액 상위 {result_count}개 종목"
        elif "상승" in message:
            return f"상승률 상위 {result_count}개 종목"
        elif "하락" in message:
            return f"하락률 상위 {result_count}개 종목"

    if "RSI" in message.upper():
        if "30" in message or "이하" in message:
            return f"RSI 과매도 종목 ({result_count}개)"
        elif "70" in message or "이상" in message:
            return f"RSI 과매수 종목 ({result_count}개)"

    if "외국인" in message:
        if "매수" in message:
            return f"외국인 순매수 종목 ({result_count}개)"
        elif "매도" in message:
            return f"외국인 순매도 종목 ({result_count}개)"

    if "기관" in message:
        if "매수" in message:
            return f"기관 순매수 종목 ({result_count}개)"
        elif "매도" in message:
            return f"기관 순매도 종목 ({result_count}개)"

    # Fallback to intent-based title
    base_title = intent_titles.get(intent, "조회 결과")
    return f"{base_title} ({result_count}개)"


def format_table_visualization(
    results: List[Dict[str, Any]],
    title: str = "",
    limit: int = 50,
    market: str = "KR"
) -> Optional[Dict[str, Any]]:
    """
    Format query results as visualization table data for frontend rendering.

    Args:
        results: List of result dictionaries
        title: Table title
        limit: Maximum rows to include
        market: Market type (KR/US) for unit formatting

    Returns:
        Visualization data dict or None if no results
    """
    if not results:
        return None

    # Get original column keys
    original_columns = list(results[0].keys())

    # Translate headers to Korean with market-specific units
    translated_headers = []
    for col in original_columns:
        base_name = translate_column_name(col)

        # Add currency units based on market and column type
        if col in ["close", "open", "high", "low", "price", "current_price"]:
            if market == "US":
                base_name = f"{base_name}($)"
            else:
                base_name = f"{base_name}(원)"
        elif col in ["market_cap", "estimated_market_cap"]:
            if market == "US":
                base_name = f"{base_name}(억$)"
            else:
                base_name = f"{base_name}(억원)"
        elif col in ["trading_value"]:
            if market == "US":
                base_name = f"{base_name}($)"
            else:
                base_name = f"{base_name}(원)"
        elif col in ["change_rate", "change_pct"]:
            base_name = f"{base_name}"  # Already has (%) in translation

        translated_headers.append(base_name)

    # Build rows with raw values (formatting done in frontend)
    rows = []
    for row in results[:limit]:
        row_data = []
        for col in original_columns:
            val = row.get(col)
            if val is None:
                row_data.append(None)
            elif isinstance(val, (int, float)):
                # Convert large floats to int to avoid scientific notation in JSON
                if isinstance(val, float) and abs(val) >= 1e10:
                    row_data.append(int(val))
                else:
                    row_data.append(val)
            else:
                row_data.append(str(val))
        rows.append(row_data)

    return {
        "type": "table",
        "title": title,
        "data": {
            "headers": translated_headers,
            "rows": rows,
            "total_count": len(results),
            "displayed_count": len(rows)
        }
    }


def get_template_for_intent(intent: str, sub_type: Optional[str] = None) -> str:
    """
    Get appropriate response template based on intent

    Args:
        intent: User intent (ranking, technical, filter, etc.)
        sub_type: Specific sub-type within the intent

    Returns:
        Template string for response guidance
    """
    template_info = get_template_by_intent(intent, sub_type)

    if template_info:
        return template_info.get("template", "")

    # Default template for unknown intents
    return """## Query Results

{result_table}

### Summary
- Provide key insights from the data
- Highlight important patterns or outliers

{disclaimer}"""


def detect_template_subtype(intent: str, question: str, state: Dict = None) -> Optional[str]:
    """
    Detect specific template subtype based on question content

    Args:
        intent: User intent
        question: User question
        state: Current graph state (used to check stock_codes for analysis pattern)

    Returns:
        Template subtype key or None
    """
    question_lower = question.lower()

    # Investment strategy question detection (priority check)
    strategy_keywords = [
        "사도돼", "살까", "살만", "사야", "매수해도", "들어가도", "진입",
        "오를까", "오르나", "올라갈까",
        "팔아도", "팔까", "팔아야", "매도해도",
        "내릴까", "내리나", "떨어질까", "빠질까",
        "괜찮을까", "어떨까", "시나리오", "목표가", "손절가",
        "가져가", "홀딩", "보유", "들고", "유지할까", "갖고있어도",
        "팔지 말", "안 팔아도",
        "단타", "장투", "장기투자", "스윙",
        "물린", "본전",
    ]
    if any(kw in question_lower for kw in strategy_keywords):
        return "investment_strategy"

    # "(stock name) + analysis" pattern: only when stock codes exist
    analysis_keywords = ["분석"]
    if state and state.get("entities", {}).get("stock_codes"):
        if any(kw in question_lower for kw in analysis_keywords):
            return "investment_strategy"

    # Technical indicator subtypes
    if intent == "technical":
        if "rsi" in question_lower:
            if "30" in question_lower or "과매도" in question_lower:
                return "rsi_oversold"
            elif "70" in question_lower or "과매수" in question_lower:
                return "rsi_overbought"
        elif "macd" in question_lower and ("골든" in question_lower or "golden" in question_lower):
            return "macd_golden_cross"
        elif "볼린저" in question_lower or "bollinger" in question_lower:
            if "상단" in question_lower or "upper" in question_lower:
                return "bollinger_upper_break"
            elif "하단" in question_lower or "lower" in question_lower:
                return "bollinger_lower_break"
        elif "정배열" in question_lower:
            return "ma_alignment_bullish"
        elif "역배열" in question_lower:
            return "ma_alignment_bearish"

    # Ranking subtypes
    elif intent == "ranking":
        if "거래대금" in question_lower:
            if "평균" in question_lower:
                return "trading_value_avg"
            return "trading_value_top"
        elif "시가총액" in question_lower or "시총" in question_lower:
            return "market_cap_top"
        elif "거래량" in question_lower:
            return "volume_top"
        elif "상승" in question_lower:
            return "change_rate_top"
        elif "하락" in question_lower:
            return "change_rate_bottom"

    # Investor subtypes
    elif intent == "investor":
        if "외국인" in question_lower:
            if "매도" in question_lower:
                return "foreign_net_sell"
            return "foreign_net_buy"
        elif "기관" in question_lower:
            return "institution_net_buy"
        elif "동반" in question_lower or "쌍끌이" in question_lower:
            return "foreign_institution_both"

    # Quant subtypes
    elif intent == "quant":
        if "가치" in question_lower:
            return "value_grade_top"
        elif "모멘텀" in question_lower:
            return "momentum_grade_top"
        elif "퀄리티" in question_lower and "가치" in question_lower:
            return "quality_value_both"
        return "total_grade_top"

    # Market subtypes
    elif intent == "market":
        if "코스피" in question_lower:
            return "kospi_index"
        elif "코스닥" in question_lower:
            return "kosdaq_index"
        elif "나스닥" in question_lower or "s&p" in question_lower or "다우" in question_lower:
            return "us_index"

    # Macro subtypes
    elif intent == "macro":
        if "금리" in question_lower:
            if "국채" in question_lower:
                return "treasury_yield"
            return "fed_rate"
        elif "cpi" in question_lower or "물가" in question_lower:
            return "us_cpi"
        elif "실업" in question_lower:
            return "unemployment"
        elif "vix" in question_lower or "공포" in question_lower:
            return "vix_index"

    return None


def _calculate_data_summary(results: List[Dict[str, Any]]) -> str:
    """
    Calculate data summary including date range from ALL results.

    This ensures the LLM knows the full data period even when
    only a subset of rows is displayed (due to limit).

    Args:
        results: All query results

    Returns:
        Data summary string for prompt
    """
    if not results:
        return ""

    total_rows = len(results)
    summary_parts = [f"[Data Summary: {total_rows} rows total]"]

    # Find date column and calculate range
    date_columns = {"date", "time", "datetime", "timestamp", "trading_date", "trade_date"}
    date_col = None

    for col in results[0].keys():
        if col.lower() in date_columns:
            date_col = col
            break

    if date_col:
        # Extract all dates
        dates = []
        for row in results:
            date_val = row.get(date_col)
            if date_val is not None:
                dates.append(date_val)

        if dates:
            min_date = min(dates)
            max_date = max(dates)
            summary_parts.append(f"Period: {min_date} ~ {max_date}")

    return " | ".join(summary_parts)


def format_sub_query_results(sub_query_results: List[Dict[str, Any]]) -> str:
    """
    Format sub-query results from parallel_sql_pipeline as supplementary context.

    Skips the primary result (largest result set) since it's already in the main
    query_result. Only includes additional sub-query results as context.

    Args:
        sub_query_results: List of sub-query result dicts from parallel_sql_pipeline

    Returns:
        Formatted string for inclusion in LLM prompt, or empty string if no additional data
    """
    if not sub_query_results:
        return ""

    sections = []
    for i, sq in enumerate(sub_query_results):
        question = sq.get("question", "")
        result_data = sq.get("result", [])
        error = sq.get("error")
        result_count = sq.get("result_count", 0)

        if error:
            sections.append(f"### Sub-query: {question}\nStatus: Failed ({error[:100]})")
            continue

        if not result_data:
            sections.append(f"### Sub-query: {question}\nStatus: No data returned")
            continue

        # Format result data (limit rows for prompt size)
        display_rows = result_data[:10]
        if display_rows:
            headers = list(display_rows[0].keys())
            header_line = " | ".join(headers)
            rows_text = []
            for row in display_rows:
                row_values = []
                for h in headers:
                    val = row.get(h, "")
                    if isinstance(val, float):
                        val = f"{val:,.2f}"
                    elif isinstance(val, int) and abs(val) > 1000:
                        val = f"{val:,}"
                    else:
                        val = str(val) if val is not None else ""
                    # Truncate long values
                    if len(val) > 30:
                        val = val[:27] + "..."
                    row_values.append(val)
                rows_text.append(" | ".join(row_values))

            data_text = f"{header_line}\n" + "\n".join(rows_text)
            if result_count > 10:
                data_text += f"\n... ({result_count} total rows)"

            sections.append(f"### Sub-query: {question}\n{data_text}")

    if not sections:
        return ""

    return "## Additional Query Results (from parallel sub-queries)\n\n" + "\n\n".join(sections)


async def generate_response_with_llm(
    question: str,
    results: List[Dict[str, Any]],
    intent: str,
    provider: str = None,
    model: str = None,
    state: Dict[str, Any] = None
) -> str:
    """
    Generate natural language response using LLM with template guidance and explainability

    Args:
        question: Original user question
        results: Query results
        intent: User intent
        provider: LLM provider
        model: Model name
        state: Graph state for explainability (data sources, confidence)

    Returns:
        Natural language response with explainability sections
    """
    try:
        # Get LLM
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        # Format results for prompt
        if results:
            # Calculate data summary (date range, row count) from ALL results before limit
            data_summary = _calculate_data_summary(results)

            # Format table with limit for display
            results_text = format_table_response(results, limit=15)

            # Add data summary at the beginning
            results_text = f"{data_summary}\n\n{results_text}"
        else:
            results_text = "No data found."

        # Calculate financial metrics from results
        market = state.get("market", "KR") if state else "KR"
        metrics = calculate_financial_metrics(results)
        metrics_text = format_metrics_for_prompt(metrics, market=market)

        # Build explainability information from state
        explainability_info = format_explainability_for_prompt(state)

        # Get appropriate template based on intent and question
        sub_type = detect_template_subtype(intent, question, state)
        response_template = get_template_for_intent(intent, sub_type)

        # Get supplementary context from context_enricher node
        supplementary_context = state.get("supplementary_context", "") if state else ""
        if not supplementary_context:
            supplementary_context = "No supplementary context available."

        # Append sub_query_results context if available (from parallel_sql_pipeline)
        if state and state.get("sub_query_results"):
            sub_results_text = format_sub_query_results(state["sub_query_results"])
            if sub_results_text:
                supplementary_context += "\n\n" + sub_results_text

        # Extract available columns from results (aggregate from all sources)
        all_columns = set()
        if results:
            all_columns.update(results[0].keys())
        if state and state.get("sub_query_results"):
            for sq in state["sub_query_results"]:
                sq_result = sq.get("result", [])
                if sq_result and isinstance(sq_result[0], dict):
                    all_columns.update(sq_result[0].keys())
        available_columns = ", ".join(sorted(all_columns)) if all_columns else "none"

        # Create prompt with template guidance, calculated metrics, and explainability
        prompt = RESPONSE_GENERATION_PROMPT.format(
            question=question,
            results=results_text,
            calculated_metrics=metrics_text,
            explainability_info=explainability_info,
            supplementary_context=supplementary_context,
            response_template=response_template,
            available_columns=available_columns
        )

        # Get response
        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        return response_text.strip()

    except Exception as e:
        logger.error(f"[ResponseGenerator] LLM generation error: {e}")
        raise


CHAT_RESPONSE_PROMPT = """You are Alpha AI, a friendly and knowledgeable assistant.

Respond naturally and helpfully in Korean to the user's message.

## What You Can Answer
- General questions: date, time, weather, greetings, basic math calculations
- Financial concepts: RSI, MACD, PER, PBR, bollinger bands, moving averages, etc.
- General knowledge questions within your training data
- Service usage guidance and capabilities
- Explanations of stock market terminology and investment concepts

## Guidelines
- Answer directly and naturally like a helpful assistant
- For questions requiring real-time stock data, guide the user to ask specific queries
  (e.g., "삼성전자 현재가를 알고 싶으시면 '삼성전자 주가 알려줘'라고 질문해 주세요")
- Do not use emojis
- Be helpful, informative, and conversational
- If you don't know something, say so honestly

## User Message
{message}

## Response (in Korean):"""


FALLBACK_RESPONSE_PROMPT = """You are Alpha AI, a helpful financial assistant.

The user asked a question, but the database query failed or returned no results.
Try to provide a helpful response based on your knowledge.

## User Question
{message}

## Query Status
- Intent: {intent}
- Error: {error}

## Guidelines
- If the question is about general concepts (e.g., "RSI가 뭐야?"), explain the concept
- If the question requires specific real-time data that you cannot provide, explain why and suggest alternatives
- If the question is about a specific stock but data is unavailable, provide general guidance
- Be honest about limitations
- Do not use emojis
- Respond in Korean

## Response (in Korean):"""


def _has_external_data(state: Dict[str, Any]) -> bool:
    """Check if external data (news, disclosures, web search) exists in state."""
    news_data = state.get("news_data", [])
    disclosure_data = state.get("disclosure_data", [])
    web_search_data = state.get("web_search_data", [])
    return bool(news_data or disclosure_data or web_search_data)


NEWS_SUMMARY_PROMPT = """다음 뉴스 기사들을 3-4문장으로 요약해주세요.
핵심 사실과 시장에 미치는 영향을 중심으로 작성하세요.
이모지를 사용하지 마세요.

뉴스:
{news_text}

요약:"""


async def _summarize_news(news_items: list) -> Optional[str]:
    """
    Summarize news articles using GPT-4o-mini.

    Returns:
        Summary string, or None on failure (caller falls back to title listing)
    """
    if not news_items:
        return None

    try:
        from core.llm.factory import get_llm, LLMProvider

        news_lines = []
        for i, item in enumerate(news_items, 1):
            title = item.get("title", "")
            snippet = item.get("snippet", item.get("description", ""))
            source = item.get("source", "")
            date = item.get("date", "")
            news_lines.append(f"{i}. [{source}, {date}] {title}\n   {snippet}")

        news_text = "\n".join(news_lines)
        prompt = NEWS_SUMMARY_PROMPT.format(news_text=news_text)

        llm = get_llm(LLMProvider.OPENAI, model_name="gpt-4o-mini")
        response = await llm.ainvoke(prompt, max_tokens=800)

        content = response.content if hasattr(response, "content") else str(response)
        content = content.strip()

        if content:
            logger.info(f"[ResponseGenerator] News summarized: {len(content)} chars from {len(news_items)} articles")
            return content
        return None
    except Exception as e:
        logger.warning(f"[ResponseGenerator] News summarization failed, using fallback: {e}")
        return None


async def _format_external_data_as_reference(state: Dict[str, Any]) -> Optional[str]:
    """
    Format external data (news, disclosures) as a reference section.
    News articles are summarized using GPT-4o-mini for concise overview.

    Args:
        state: Graph state containing news_data and disclosure_data

    Returns:
        Formatted reference string, or None if no data
    """
    news_data = state.get("news_data", [])
    disclosure_data = state.get("disclosure_data", [])

    if not news_data and not disclosure_data:
        return None

    sections = []

    if news_data:
        news_summary = await _summarize_news(news_data[:5])
        if news_summary:
            sections.append("-- 관련 뉴스 요약 --\n" + news_summary)
        else:
            # Fallback: title listing if summarization fails
            news_lines = []
            for i, item in enumerate(news_data[:5], 1):
                title = item.get("title", "")
                link = item.get("link", "")
                source = item.get("source", "")
                date = item.get("date", "")
                if link:
                    news_lines.append(f"{i}. [{title}]({link}) ({source}, {date})")
                else:
                    news_lines.append(f"{i}. {title} ({source}, {date})")
            sections.append("-- 관련 뉴스 --\n" + "\n".join(news_lines))

    if disclosure_data:
        disc_lines = []
        for i, item in enumerate(disclosure_data[:5], 1):
            report_nm = item.get("report_nm", item.get("title", ""))
            corp_name = item.get("corp_name", "")
            date = item.get("rcept_dt", item.get("date", ""))
            pblntf_ty = item.get("pblntf_ty", "")
            if pblntf_ty:
                disc_lines.append(f"{i}. [{pblntf_ty}] {report_nm} ({corp_name}, {date})")
            else:
                disc_lines.append(f"{i}. {report_nm} ({corp_name}, {date})")
        sections.append("-- 관련 공시 --\n" + "\n".join(disc_lines))

    if not sections:
        return None

    return "\n\n[참고 자료]\n" + "\n\n".join(sections)


EXTERNAL_DATA_RESPONSE_PROMPT = """You are Alpha AI, a financial assistant specialized in stock market analysis.

The user asked a question. No database results are available, but external data (news, disclosures) has been collected.
Analyze the external data and provide a comprehensive, well-structured response.

## User Question
{message}

## Intent
{intent}

## News Data ({news_count} articles)
{news_text}

## News Sentiment
{sentiment_text}

## Disclosure Data ({disclosure_count} items)
{disclosure_text}

## Guidelines
- Synthesize the collected news and disclosures into a coherent analysis
- Highlight key facts: earnings, price movements, analyst opinions, market reactions
- If sentiment data is available, include the overall market sentiment
- Structure the response with clear sections
- Be specific with numbers, dates, and sources when available
- Do not fabricate data not present in the provided sources
- Do not use emojis
- Respond in Korean

## Response (in Korean):"""


async def generate_external_data_response(
    message: str,
    intent: str,
    state: Dict[str, Any],
    provider: str = None,
    model: str = None
) -> str:
    """Generate response based on external data (news, disclosures) when no DB results exist."""
    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        # Format news data
        news_data = state.get("news_data", [])
        if news_data:
            news_lines = []
            for i, item in enumerate(news_data[:15], 1):
                title = item.get("title", "")
                source = item.get("source", "")
                date = item.get("date", "")
                snippet = item.get("snippet", item.get("description", ""))
                news_lines.append(f"{i}. [{source}] {title} ({date})\n   {snippet}")
            news_text = "\n".join(news_lines)
        else:
            news_text = "No news data available."

        # Format sentiment
        news_sentiment = state.get("news_sentiment")
        if news_sentiment:
            overall = news_sentiment.get("overall", "NEUTRAL")
            confidence = news_sentiment.get("confidence", "LOW")
            pos = news_sentiment.get("positive_count", 0)
            neg = news_sentiment.get("negative_count", 0)
            neu = news_sentiment.get("neutral_count", 0)
            sentiment_text = f"Overall: {overall} (Confidence: {confidence}), Positive: {pos}, Negative: {neg}, Neutral: {neu}"
        else:
            sentiment_text = "No sentiment analysis available."

        # Format disclosure data
        disclosure_data = state.get("disclosure_data", [])
        if disclosure_data:
            disc_lines = []
            for i, item in enumerate(disclosure_data[:10], 1):
                title = item.get("report_nm", item.get("title", ""))
                date = item.get("rcept_dt", item.get("date", ""))
                corp = item.get("corp_name", "")
                disc_lines.append(f"{i}. [{corp}] {title} ({date})")
            disclosure_text = "\n".join(disc_lines)
        else:
            disclosure_text = "No disclosure data available."

        prompt = EXTERNAL_DATA_RESPONSE_PROMPT.format(
            message=message,
            intent=intent,
            news_count=len(news_data),
            news_text=news_text,
            sentiment_text=sentiment_text,
            disclosure_count=len(disclosure_data),
            disclosure_text=disclosure_text
        )

        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        return response_text.strip()

    except Exception as e:
        logger.error(f"[ResponseGenerator] External data response failed: {e}")
        raise


async def generate_fallback_llm_response(
    message: str,
    intent: str,
    error: str = None,
    provider: str = None,
    model: str = None
) -> str:
    """
    Generate fallback response using LLM when SQL fails or returns no results.

    Args:
        message: User's original message
        intent: Detected intent
        error: Error message if any
        provider: LLM provider
        model: Model name

    Returns:
        Fallback response from LLM
    """
    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        error_text = error if error else "No data found"

        prompt = FALLBACK_RESPONSE_PROMPT.format(
            message=message,
            intent=intent,
            error=error_text
        )

        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        return response_text.strip()

    except Exception as e:
        logger.error(f"[ResponseGenerator] Fallback LLM response failed: {e}")
        return "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다. 질문을 다시 시도해 주세요."


async def generate_chat_response(
    message: str,
    provider: str = None,
    model: str = None
) -> str:
    """
    Generate direct conversational response using LLM for chat intent.

    Args:
        message: User's message
        provider: LLM provider
        model: Model name

    Returns:
        Natural language response
    """
    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        prompt = CHAT_RESPONSE_PROMPT.format(message=message)

        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        return response_text.strip()

    except Exception as e:
        logger.error(f"[ResponseGenerator] Chat response generation failed: {e}")
        return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 다시 시도해 주세요."


def generate_fallback_response(
    results: List[Dict[str, Any]],
    intent: str,
    result_count: int,
    sql_error: str = None
) -> str:
    """
    Generate fallback response without LLM

    Args:
        results: Query results
        intent: User intent
        result_count: Number of results
        sql_error: SQL error if any

    Returns:
        Formatted response string
    """
    if sql_error:
        return f"Query execution failed: {sql_error}\n\nPlease try rephrasing your question."

    if not results or result_count == 0:
        return "No data found matching your query."

    # Generate summary based on intent
    if intent == "ranking":
        summary = f"Top {result_count} results:\n\n"
    elif intent == "filter":
        summary = f"Found {result_count} items matching your criteria:\n\n"
    elif intent == "market":
        summary = "Market index data:\n\n"
    else:
        summary = f"Query results ({result_count} rows):\n\n"

    # Format table
    table = format_table_response(results)

    return summary + table


def validate_response_data_consistency(
    response: str,
    query_result: List[Dict[str, Any]],
    message: str
) -> tuple:
    """
    Validate that the LLM response doesn't mention data that wasn't available.

    Args:
        response: LLM generated response
        query_result: Actual query results
        message: Original user question

    Returns:
        Tuple of (is_valid, warnings_list)
    """
    warnings = []

    if not query_result:
        return True, warnings

    # Get available columns from query result
    available_columns = set()
    if query_result and len(query_result) > 0:
        available_columns = set(query_result[0].keys())

    # Define data terms that require actual data
    data_term_to_columns = {
        "ROE": ["roe", "return_on_equity"],
        "ROA": ["roa", "return_on_assets"],
        "EPS": ["eps", "earnings_per_share"],
        "BPS": ["bps", "book_value_per_share"],
        "PER": ["per", "price_earnings_ratio", "p_e_ratio"],
        "PBR": ["pbr", "price_book_ratio", "p_b_ratio"],
        "배당률": ["dividend_yield", "dividend_rate", "dps"],
        "dividend": ["dividend_yield", "dividend_rate", "dps"],
        "부채비율": ["debt_ratio", "debt_to_equity"],
        "영업이익": ["operating_income", "operating_profit"],
        "순이익": ["net_income", "net_profit"],
    }

    response_upper = response.upper()

    for term, required_columns in data_term_to_columns.items():
        # Check if term is mentioned in response
        if term.upper() in response_upper:
            # Check if any required column exists in query result
            has_data = any(col in available_columns for col in required_columns)
            if not has_data:
                warnings.append(f"{term} data was mentioned but not available in query results")
                logger.warning(f"[ResponseValidator] {term} mentioned but columns {required_columns} not in {available_columns}")

    return len(warnings) == 0, warnings


def add_data_availability_warning(response: str, warnings: List[str]) -> str:
    """
    Add warning about data availability to response if needed.

    Args:
        response: Original response
        warnings: List of warnings

    Returns:
        Response with warnings appended if any
    """
    if not warnings:
        return response

    warning_text = "\n\n---\n[Data Availability Notice]\n"
    for warning in warnings:
        warning_text += f"- {warning}\n"

    # Insert before the disclaimer if present
    disclaimer_marker = "※ 본 서비스가 제공하는"
    if disclaimer_marker in response:
        parts = response.split(disclaimer_marker)
        return parts[0] + warning_text + disclaimer_marker + parts[1]

    return response + warning_text


def _apply_both_market_limit(
    data: List[Dict[str, Any]],
    market: str,
    entities: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    When market=BOTH, enforce user-requested LIMIT by splitting:
    KR = ceil(limit/2), US = floor(limit/2).
    Total always equals the original limit.
    """
    if market != "BOTH" or not entities:
        return data

    limit = entities.get("limit")
    if not limit or len(data) <= limit:
        return data

    # Find market column
    market_col = None
    if data:
        for key in data[0].keys():
            if key.lower() == "market":
                market_col = key
                break

    if not market_col:
        logger.warning(
            "[ResponseGenerator] BOTH market requested but no market column in data, skipping limit split"
        )
        return data

    kr_limit = math.ceil(limit / 2)
    us_limit = limit - kr_limit  # floor

    kr_rows = [r for r in data if str(r.get(market_col, "")).upper() == "KR"]
    us_rows = [r for r in data if str(r.get(market_col, "")).upper() == "US"]

    result = kr_rows[:kr_limit] + us_rows[:us_limit]

    logger.info(
        f"[ResponseGenerator] BOTH market limit applied: "
        f"{len(data)} -> {len(result)} (KR={min(len(kr_rows), kr_limit)}, US={min(len(us_rows), us_limit)})"
    )
    return result


# Chart data point limits per chart type
CHART_MAX_POINTS = {
    "line_chart": 200,
    "candlestick": 120,
    "bar_chart": 30,
    "pie_chart": 20,
    "multi_chart": 30,
    "table": 50,
}

DATE_COLUMNS = {"date", "trade_date", "trading_date", "created_at", "updated_at"}


def _find_date_column(columns: List[str]) -> Optional[str]:
    """Find date column from column list."""
    for col in columns:
        if col.lower() in DATE_COLUMNS:
            return col
    return None


def _limit_data_points(
    data: List[Dict[str, Any]],
    max_points: int = 200
) -> List[Dict[str, Any]]:
    """
    Limit data points for chart visualization.
    Takes the most recent N items (data must be sorted by date ASC).
    """
    if not data or len(data) <= max_points:
        return data
    return data[-max_points:]


async def response_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate natural language response from query results

    Args:
        state: Current graph state with query results

    Returns:
        Updated state with 'response' and 'response_type' fields
    """
    logger.info("[AlphaAI:ResponseGenerator] Processing...")

    message = state.get("message", "")
    intent = state.get("intent", "query")
    query_result = state.get("query_result")
    result_count = state.get("result_count", 0)

    # BOTH market limit enforcement
    if query_result and result_count > 0:
        market = state.get("market", "KR")
        entities_for_limit = state.get("entities") or {}
        query_result = _apply_both_market_limit(query_result, market, entities_for_limit)
        result_count = len(query_result)

    sql_error = state.get("sql_error")
    provider = state.get("provider")
    model = state.get("model_name")

    # Handle chat/explain intent - direct LLM response without SQL
    if intent in ["chat", "explain"]:
        try:
            response = await generate_chat_response(
                message=message,
                provider=provider,
                model=model
            )
            response_type = "text"
            logger.info(f"[AlphaAI:ResponseGenerator] Chat response generated, length: {len(response)}")
        except Exception as e:
            logger.error(f"[ResponseGenerator] Chat response failed: {e}")
            response = "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
            response_type = "error"

    # Handle SQL errors - try fallback LLM response
    elif sql_error:
        logger.warning(f"[AlphaAI:ResponseGenerator] SQL error, trying fallback: {sql_error}")
        try:
            response = await generate_fallback_llm_response(
                message=message,
                intent=intent,
                error=sql_error,
                provider=provider,
                model=model
            )
            response_type = "text"
            logger.info(f"[AlphaAI:ResponseGenerator] Fallback response generated for SQL error")
        except Exception as e:
            logger.error(f"[ResponseGenerator] Fallback also failed: {e}")
            response = f"죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.\n\n질문을 다르게 표현해 주세요."
            response_type = "error"

    # Handle no DB results but external data exists - generate response from external data
    elif (query_result is None or result_count == 0) and _has_external_data(state):
        news_count = len(state.get("news_data", []))
        disc_count = len(state.get("disclosure_data", []))
        logger.info(f"[AlphaAI:ResponseGenerator] No DB results, but external data found (news={news_count}, disclosures={disc_count})")
        try:
            response = await generate_external_data_response(
                message=message,
                intent=intent,
                state=state,
                provider=provider,
                model=model
            )
            response_type = "text"
            logger.info(f"[AlphaAI:ResponseGenerator] External data response generated, length: {len(response)}")
        except Exception as e:
            logger.warning(f"[ResponseGenerator] External data response failed, trying fallback: {e}")
            response = await generate_fallback_llm_response(
                message=message,
                intent=intent,
                error="External data processing failed",
                provider=provider,
                model=model
            )
            response_type = "text"

    # Handle no primary results - check sub_query_results before fallback
    elif query_result is None or result_count == 0:
        sub_query_results = state.get("sub_query_results", [])
        has_sub_data = any(sq.get("result_count", 0) > 0 for sq in sub_query_results)

        if has_sub_data:
            # Sub-query results have data - use LLM generation path
            logger.info(
                f"[AlphaAI:ResponseGenerator] Primary empty but sub_query_results have data, "
                f"using LLM generation path"
            )
            try:
                response = await generate_response_with_llm(
                    question=message,
                    results=[],
                    intent=intent,
                    provider=provider,
                    model=model,
                    state=state
                )
                response_type = "table"
                logger.info(f"[AlphaAI:ResponseGenerator] LLM response from sub_query_results, length: {len(response)}")
            except Exception as e:
                logger.warning(f"[ResponseGenerator] Sub-query primary LLM failed: {e}")
                try:
                    logger.info("[ResponseGenerator] Retrying sub-query with GPT-4.1 fallback...")
                    response = await generate_response_with_llm(
                        question=message,
                        results=[],
                        intent=intent,
                        provider="openai",
                        model="gpt-4.1",
                        state=state
                    )
                    response_type = "text"
                    logger.info(f"[AlphaAI:ResponseGenerator] GPT-4.1 sub-query fallback, length: {len(response)}")
                except Exception as e2:
                    logger.warning(f"[ResponseGenerator] GPT-4.1 sub-query fallback also failed: {e2}")
                    response = await generate_fallback_llm_response(
                        message=message,
                        intent=intent,
                        error="No data found matching your query",
                        provider=provider,
                        model=model
                    )
                    response_type = "text"
        else:
            logger.info("[AlphaAI:ResponseGenerator] No results found, trying fallback")
            try:
                response = await generate_fallback_llm_response(
                    message=message,
                    intent=intent,
                    error="No data found matching your query",
                    provider=provider,
                    model=model
                )
                response_type = "text"
                logger.info(f"[AlphaAI:ResponseGenerator] Fallback response generated for no results")
            except Exception as e:
                logger.error(f"[ResponseGenerator] Fallback failed: {e}")
                response = "검색 결과가 없습니다. 질문을 다르게 표현해 주세요."
                response_type = "text"

    else:
        try:
            # Generate response with LLM (including explainability from state)
            response = await generate_response_with_llm(
                question=message,
                results=query_result,
                intent=intent,
                provider=provider,
                model=model,
                state=state  # Pass state for explainability
            )
            response_type = "table"
            logger.info(f"[AlphaAI:ResponseGenerator] LLM response generated, length: {len(response)}")

            # Validate response data consistency (detect hallucinated data mentions)
            is_valid, warnings = validate_response_data_consistency(response, query_result, message)
            if not is_valid:
                logger.warning(f"[ResponseGenerator] Data consistency warnings: {warnings}")

        except Exception as e:
            logger.warning(f"[ResponseGenerator] Primary LLM failed: {e}")
            try:
                logger.info("[ResponseGenerator] Retrying with GPT-4.1 fallback...")
                response = await generate_response_with_llm(
                    question=message,
                    results=query_result,
                    intent=intent,
                    provider="openai",
                    model="gpt-4.1",
                    state=state
                )
                response_type = "table"
                logger.info(f"[AlphaAI:ResponseGenerator] GPT-4.1 fallback response, length: {len(response)}")
            except Exception as e2:
                logger.warning(f"[ResponseGenerator] GPT-4.1 fallback also failed: {e2}, using template")
                response = generate_fallback_response(query_result, intent, result_count)
                response_type = "table"

    # Generate visualization data using hybrid approach
    # 1. Keyword matching from question
    # 2. Data structure analysis
    # 3. Default fallback to table
    visualization = None
    if query_result and result_count > 0:
        # Get column names from first result
        columns = list(query_result[0].keys()) if query_result else []
        market = state.get("market", "KR")

        # Extract indicators from entity_extractor for multi-indicator detection
        viz_entities = state.get("entities") or {}
        indicators = viz_entities.get("indicators", [])

        # Determine chart type using hybrid resolver
        chart_type = visualization_resolver.resolve(
            question=message,
            columns=columns,
            data=query_result,
            intent=intent,
            indicators=indicators
        )

        # Check if visualization should be generated
        if visualization_resolver.should_visualize(query_result, chart_type):
            # Generate title based on intent and message
            viz_title = _generate_visualization_title(
                message, intent, result_count,
                sub_query_question=state.get("primary_sub_query_question", ""),
            )

            # Format data for the determined chart type
            if chart_type == "table":
                # Use existing table formatter for backward compatibility
                visualization = format_table_visualization(
                    results=query_result,
                    title=viz_title,
                    limit=50,
                    market=market
                )
            else:
                # Limit to most recent N data points (data already sorted ASC by sql_executor)
                max_pts = CHART_MAX_POINTS.get(chart_type, 100)
                limited_data = _limit_data_points(query_result, max_points=max_pts)

                visualization = chart_data_formatter.format(
                    chart_type=chart_type,
                    columns=columns,
                    data=limited_data,
                    title=viz_title,
                    market=market,
                    indicators=indicators
                )

            if visualization:
                viz_type = visualization.get('type', 'unknown')
                if viz_type == 'table':
                    row_count = len(visualization.get('data', {}).get('rows', []))
                    logger.info(f"[AlphaAI:ResponseGenerator] Visualization generated: {viz_type}, {row_count} rows")
                elif viz_type == 'multi_chart':
                    chart_count = len(visualization.get('data', {}).get('charts', []))
                    logger.info(f"[AlphaAI:ResponseGenerator] Visualization generated: {viz_type}, {chart_count} charts")
                else:
                    data_info = visualization.get('data', {})
                    label_count = len(data_info.get('labels', []))
                    logger.info(f"[AlphaAI:ResponseGenerator] Visualization generated: {viz_type}, {label_count} data points")

    # Append stock fallback guide message when no stock was found
    entities = state.get("entities", {})
    if entities and entities.get("stock_fallback_guide"):
        guide_msg = ("\n\n참고: 종목명이 포함된 질문을 해주시면 더 정확한 분석 결과를 "
                     "제공해 드릴 수 있습니다. (예: '삼성전자 RSI 분석해줘')")
        response = response + guide_msg

    # Apply markdown removal and numbering fix to ALL response paths
    # remove_markdown_formatting() calls fix_numbering_hierarchy() internally
    if response:
        response = remove_markdown_formatting(response)

    # Programmatically ensure LEGAL_DISCLAIMER is always appended to ALL responses
    # This guarantees disclaimer presence regardless of LLM behavior or response path
    if response:
        from .hybrid_analyzer import LEGAL_DISCLAIMER
        disclaimer_marker = "자본시장과 금융투자업에 관한 법률"
        if disclaimer_marker not in response:
            response = response.rstrip() + "\n\n" + LEGAL_DISCLAIMER.strip()

    # Append external data reference (insert before disclaimer)
    # Use marker-based insertion because LLM may generate its own disclaimer variant
    # that doesn't exactly match LEGAL_DISCLAIMER text
    if state.get("data_source") == "hybrid" and _has_external_data(state):
        external_ref = await _format_external_data_as_reference(state)
        if external_ref:
            disclaimer_marker = "※ 본 서비스"
            marker_pos = response.find(disclaimer_marker)
            if marker_pos > 0:
                # Capture preceding "---" separator if present
                prefix = response[:marker_pos].rstrip()
                if prefix.endswith("---"):
                    insert_pos = len(prefix) - 3
                    prefix = prefix[:-3].rstrip()
                else:
                    insert_pos = marker_pos
                response = prefix + "\n\n" + external_ref + "\n\n" + response[insert_pos:]
            else:
                response = response + "\n\n" + external_ref

    # Build supplementary technical indicator charts (post-query)
    supplementary_charts = None
    few_shot_examples = state.get("few_shot_examples")
    if query_result and result_count and result_count > 0 and few_shot_examples:
        from ...tools.supplementary_chart_builder import build_supplementary_charts
        supplementary_charts = await build_supplementary_charts(
            query_result=query_result,
            few_shot_examples=few_shot_examples,
            market=market
        )

    return {
        **state,
        "query_result": query_result,
        "result_count": result_count,
        "response": response,
        "response_type": response_type,
        "visualization": visualization,
        "supplementary_charts": supplementary_charts,
        "processing_steps": state.get("processing_steps", []) + ["response_generator"]
    }
