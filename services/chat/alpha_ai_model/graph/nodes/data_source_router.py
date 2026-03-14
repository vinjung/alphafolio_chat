# services/chat/alpha_ai_model/graph/nodes/data_source_router.py
"""
Data Source Router Node

Determines which data sources to use based on intent and query analysis.
Routes to: DB_ONLY, EXTERNAL_ONLY, or HYBRID pipeline.
"""
from typing import Dict, Any, List
from enum import Enum
from config import logger


class DataSource(str, Enum):
    """Data source types"""
    DB_ONLY = "db_only"           # Only database (quantitative)
    EXTERNAL_ONLY = "external_only"  # Only external APIs (qualitative)
    HYBRID = "hybrid"             # Both DB + external (comprehensive)


# Intent to data source mapping
INTENT_DATA_SOURCE_MAP = {
    # DB only - quantitative queries
    "SIMPLE_QUERY": DataSource.DB_ONLY,
    "RANKING": DataSource.DB_ONLY,
    "FILTER": DataSource.DB_ONLY,
    "TECHNICAL": DataSource.DB_ONLY,
    "QUANT": DataSource.DB_ONLY,
    "INVESTOR": DataSource.DB_ONLY,

    # External only - qualitative queries
    "NEWS": DataSource.EXTERNAL_ONLY,
    "DISCLOSURE": DataSource.EXTERNAL_ONLY,
    "SENTIMENT": DataSource.EXTERNAL_ONLY,

    # Hybrid - comprehensive analysis
    "ANALYSIS": DataSource.HYBRID,
    "RECOMMENDATION": DataSource.HYBRID,
    "COMPARISON": DataSource.HYBRID,
    "CAUSE_ANALYSIS": DataSource.HYBRID,
    "FORECAST": DataSource.HYBRID,

    # Default
    "GENERAL_CHAT": DataSource.EXTERNAL_ONLY,
    "SQL_QUERY": DataSource.DB_ONLY
}

# Keywords that indicate external data need
EXTERNAL_KEYWORDS = [
    # News related
    "뉴스", "news", "기사", "소식", "보도",
    # Disclosure related
    "공시", "disclosure", "발표", "보고서",
    # Analysis related
    "원인", "이유", "왜", "분석", "전망", "예측",
    "reason", "why", "analysis", "forecast",
    # Sentiment related
    "분위기", "심리", "여론", "반응", "sentiment",
    # Recommendation related
    "추천", "포트폴리오", "투자", "매수", "매도",
    "recommend", "portfolio", "buy", "sell"
]

# Keywords that indicate DB data need
DB_KEYWORDS = [
    # Price/Volume
    "현재가", "주가", "가격", "시세", "종가",
    "거래량", "거래대금", "시총", "시가총액",
    # Ranking
    "상위", "하위", "순위", "랭킹", "top", "bottom",
    # Technical
    "rsi", "macd", "볼린저", "이평", "골든크로스",
    "과매수", "과매도", "지표",
    # Investor
    "외국인", "기관", "개인", "순매수", "순매도",
    # Quant
    "등급", "점수", "퀀트", "grade", "score",
    # Quality/Risk
    "우량주", "블루칩", "대형주", "중형주", "소형주",
    "리스크", "변동성", "안정", "저변동", "고배당",
    "성장주", "가치주", "배당주"
]

# Intents that should prioritize DB queries
DB_PRIORITY_INTENTS = [
    "SIMPLE_QUERY", "RANKING", "FILTER",
    "TECHNICAL", "QUANT", "INVESTOR", "SQL_QUERY"
]


def detect_required_apis(message: str, intent: str) -> List[str]:
    """
    Detect which external APIs are needed

    Args:
        message: User message
        intent: Detected intent

    Returns:
        List of required API names
    """
    required = []
    message_lower = message.lower()

    # News keywords
    news_keywords = ["뉴스", "news", "기사", "소식", "보도", "언론"]
    if any(kw in message_lower for kw in news_keywords):
        required.append("naver")
        required.append("serper")

    # Risk/Analysis keywords - trigger comprehensive search
    risk_analysis_keywords = [
        "리스크", "위험", "요인", "risk", "문제점", "우려", "이슈",
        "악재", "호재", "전망", "리포트", "분석", "평가", "의견",
        "커뮤니티", "반응", "여론", "투자자", "개미", "설명"
    ]
    if any(kw in message_lower for kw in risk_analysis_keywords):
        if "naver" not in required:
            required.append("naver")
        if "serper" not in required:
            required.append("serper")

    # Disclosure keywords
    disclosure_keywords = ["공시", "disclosure", "발표", "보고서", "실적", "재무"]
    if any(kw in message_lower for kw in disclosure_keywords):
        required.append("dart")

    # Global/English keywords -> add serper
    global_keywords = ["글로벌", "global", "해외", "미국", "영문", "english"]
    if any(kw in message_lower for kw in global_keywords):
        if "serper" not in required:
            required.append("serper")

    # If no specific API detected but external needed
    if not required and intent in ["ANALYSIS", "RECOMMENDATION", "CAUSE_ANALYSIS"]:
        required = ["naver", "serper"]

    return required


def detect_search_scope(message: str, market: str) -> str:
    """
    Detect search scope for cross-market search

    Args:
        message: User message
        market: Detected market (KR/US)

    Returns:
        Search scope (local_only, global_only, cross_market)
    """
    message_lower = message.lower()

    # Cross-market indicators
    cross_market_keywords = [
        "글로벌", "global", "해외", "overseas",
        "미국 시각", "한국 시각", "동학개미",
        "외국인 반응", "해외 반응"
    ]

    if any(kw in message_lower for kw in cross_market_keywords):
        return "cross_market"

    # Default based on market
    if market == "US":
        return "global_only"
    else:
        return "local_only"


async def data_source_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route to appropriate data source based on intent and query

    Args:
        state: Current graph state

    Returns:
        Updated state with data_source and required_apis
    """
    logger.info("[AlphaAI:DataSourceRouter] Processing...")

    message = state.get("message", "")
    intent = state.get("intent", "")
    market = state.get("market", "KR")

    message_lower = message.lower()

    # Step 1: Check intent-based routing
    data_source = INTENT_DATA_SOURCE_MAP.get(intent, DataSource.DB_ONLY)

    # Step 2: Override based on keywords
    has_external_keywords = any(kw in message_lower for kw in EXTERNAL_KEYWORDS)
    has_db_keywords = any(kw in message_lower for kw in DB_KEYWORDS)

    if has_external_keywords and has_db_keywords:
        data_source = DataSource.HYBRID
    elif has_external_keywords and not has_db_keywords:
        # DB priority intent should use HYBRID instead of EXTERNAL_ONLY
        if intent in DB_PRIORITY_INTENTS:
            data_source = DataSource.HYBRID
        else:
            data_source = DataSource.EXTERNAL_ONLY
    elif has_db_keywords and not has_external_keywords:
        data_source = DataSource.DB_ONLY

    # Step 3: Detect required APIs
    required_apis = []
    if data_source in [DataSource.EXTERNAL_ONLY, DataSource.HYBRID]:
        required_apis = detect_required_apis(message, intent)

    # Step 4: Detect search scope
    search_scope = "local_only"
    if data_source in [DataSource.EXTERNAL_ONLY, DataSource.HYBRID]:
        search_scope = detect_search_scope(message, market)

    # Step 5: Check if disclaimer is needed
    requires_disclaimer = intent in [
        "RECOMMENDATION", "FORECAST", "CAUSE_ANALYSIS"
    ] or any(kw in message_lower for kw in ["추천", "매수", "매도", "투자"])

    logger.info(f"[AlphaAI:DataSourceRouter] Result: {data_source.value}, "
               f"APIs: {required_apis}, Scope: {search_scope}")

    return {
        **state,
        "data_source": data_source.value,
        "required_apis": required_apis,
        "search_scope": search_scope,
        "requires_disclaimer": requires_disclaimer,
        "processing_steps": state.get("processing_steps", []) + ["data_source_router"]
    }
