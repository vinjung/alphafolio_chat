# services/chat/alpha_ai_model/graph/nodes/query_router.py
"""
Query Router Node

Routes queries:
- "chat"     : greetings, concept explanations
- "external" : pure news/disclosure queries (no DB data needed)
- "complex"  : all DB queries (decomposed by query_decomposer)

Chat/External detection uses keyword rules (0 LLM calls).
All other queries route to query_decomposer for Claude-based processing.
"""
from typing import Dict, Any, List, Optional
import re
import json
from config import logger, settings

from langchain_core.messages import HumanMessage, AIMessage


# ============================================================
# Complex query keywords (ANY match -> complex)
# ============================================================
_COMPLEX_KEYWORDS = [
    # Screening connectors
    "이고", "이면서", "하고", "동시에",
    "찾아줘", "찾아", "골라줘", "골라",
    "필터링", "스크리닝", "screening",
    # Cross-market
    "한미", "양국", "한국과 미국", "미국과 한국",
    # Chain filtering
    "중에서", "그 중", "이 중",
    # Multi-step enrichment
    "포함해서", "추가로", "더불어",
    # Complex analysis requests
    "종합 분석", "비교 분석", "전략",
    # Comparative operators requiring sub-queries
    "대비", "업종평균", "섹터평균", "시장평균",
    # Multi-factor
    "감안", "고려해서",
]

# Multi-word complex patterns (checked as phrases, used as keyword fallback)
_COMPLEX_PATTERNS = [
    r"비교해\s*줘",
    r"비교해\s*주세요",
]

# ============================================================
# Chat / Explain detection (reuse from intent_classifier.py)
# ============================================================
_CHAT_KEYWORDS = [
    "안녕", "hello", "hi ", "테스트", "test", "몇일", "몇시", "날씨",
    "고마워", "감사", "thanks", "잘가", "bye", "뭐해", "심심",
]
_CHAT_PATTERNS = ["오늘 ", "지금 ", "현재 시간", "몇 월", "무슨 요일"]

_EXPLAIN_PATTERNS = [
    "뭐야", "뭐에요", "뭔가요", "무엇인가요", "무엇이야", "이란?", "이란",
    "설명해", "what is", "explain", "이 뭐", "가 뭐", "은 뭐", "는 뭐",
    "개념", "정의", "의미",
]
_EXPLAIN_TERMS = [
    "rsi", "macd", "per", "pbr", "eps", "roe", "roa", "시가총액", "거래량",
    "볼린저", "이동평균", "골든크로스", "데드크로스", "공매도", "배당", "증거금",
]

# Stock reference indicators (if present, not a pure explain)
_STOCK_REFERENCE_INDICATORS = [
    "주가", "현재가", "가격", "종목", "005930", "삼성전자", "애플",
]

# ============================================================
# External-only keywords (reuse from data_source_router.py)
# ============================================================
_EXTERNAL_ONLY_KEYWORDS = ["뉴스", "news", "기사", "공시", "disclosure"]

# DB keywords that indicate data queries (reuse from data_source_router.py)
_DB_KEYWORDS = [
    "현재가", "주가", "가격", "시세", "종가",
    "거래량", "거래대금", "시총", "시가총액",
    "상위", "하위", "순위", "랭킹", "top", "bottom",
    "rsi", "macd", "볼린저", "이평", "골든크로스",
    "과매수", "과매도", "지표",
    "외국인", "기관", "개인", "순매수", "순매도",
    "등급", "점수", "퀀트", "grade", "score",
    "배당", "per", "pbr", "eps", "roe",
]

# ============================================================
# Hybrid keywords (reuse from query_decomposer.py)
# ============================================================
_HYBRID_KEYWORDS = [
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

# ============================================================
# Market detection keywords (reuse from intent_classifier.py)
# ============================================================
_US_KEYWORDS = [
    "미국", "나스닥", "nasdaq", "nyse", "s&p", "다우", "dow",
    "애플", "apple", "테슬라", "tesla", "구글", "google",
    "아마존", "amazon", "마이크로소프트", "microsoft", "엔비디아", "nvidia",
    "옵션", "콜옵션", "풋옵션", "풋콜비율", "put/call", "pcr",
    "vix", "빅스", "공포지수", "변동성지수",
    "내부자 거래", "내부자 매수", "내부자 매도", "insider",
    "연방기금금리", "fed fund", "연준금리", "fomc",
    "국채수익률", "treasury yield",
    "달러인덱스", "dxy", "달러지수",
]

_KR_KEYWORDS = [
    "코스피", "코스닥", "kospi", "kosdaq", "유가증권", "코넥스",
    "외국인", "외인", "기관", "개인", "개미",
    "순매수", "순매도",
    "프로그램", "프로그램 매매",
    "대량매매", "블록딜",
    "외국인 지분", "외인 지분",
    "dart", "다트", "감사보고서", "사업보고서",
    "최대주주", "대주주",
    "자사주", "자기주식",
    "리서치", "목표주가", "투자의견", "증권사 리포트",
    "삼성전자", "삼성", "현대", "네이버", "카카오",
    "셀트리온", "삼성바이오", "현대차", "기아", "포스코",
]

_BOTH_KEYWORDS = ["한미", "양국", "한국과 미국", "한국 미국", "전세계", "세계", "글로벌", "global", "worldwide"]

# ============================================================
# Intent keywords for simple path classification
# ============================================================
_RANKING_KEYWORDS = ["상위", "하위", "top", "bottom", "랭킹", "순위", "최고"]
_FILTER_KEYWORDS = ["이상", "이하", "초과", "미만", "필터", "조건"]
_TECHNICAL_KEYWORDS = ["rsi", "macd", "볼린저", "이평", "골든크로스", "데드크로스", "과매수", "과매도"]
_INVESTOR_KEYWORDS = ["외국인", "외인", "기관", "개인", "개미", "순매수", "순매도"]
_QUANT_KEYWORDS = ["등급", "grade", "점수", "score", "퀀트", "가치주", "성장주", "모멘텀"]
_MARKET_KEYWORDS = ["코스피", "코스닥", "지수", "index", "kospi", "kosdaq", "나스닥", "nasdaq"]
_ANALYSIS_KEYWORDS = [
    "분석", "전망", "동향", "추이", "진단",
    "사도돼", "살까", "오를까", "팔까", "내릴까", "괜찮을까", "어떨까",
    "매수", "매도", "진입", "시나리오", "목표가", "손절",
]

# ============================================================
# Follow-up detection
# ============================================================
_CONTEXT_SWITCH_KEYWORDS = ["그럼", "그러면", "대신", "말고"]


def _is_chat_or_explain(message_lower: str, message_len: int) -> Optional[str]:
    """Detect chat or explain intent. Returns 'chat', 'explain', or None."""
    # Chat
    if any(kw in message_lower for kw in _CHAT_KEYWORDS):
        return "chat"
    if any(p in message_lower for p in _CHAT_PATTERNS):
        return "chat"

    # Explain
    has_explain_pattern = any(p in message_lower for p in _EXPLAIN_PATTERNS)
    has_explain_term = any(t in message_lower for t in _EXPLAIN_TERMS)
    has_stock_ref = any(s in message_lower for s in _STOCK_REFERENCE_INDICATORS)

    if has_explain_pattern and has_explain_term and not has_stock_ref:
        return "explain"
    if has_explain_pattern and not has_stock_ref and message_len < 30:
        return "explain"

    return None



def _is_external_only(message_lower: str) -> bool:
    """Check if query is external-only (news/disclosure without DB need)."""
    has_external = any(kw in message_lower for kw in _EXTERNAL_ONLY_KEYWORDS)
    has_db = any(kw in message_lower for kw in _DB_KEYWORDS)
    return has_external and not has_db


def _detect_market(message_lower: str) -> str:
    """Detect market from keywords. Returns KR, US, or BOTH."""
    if any(kw in message_lower for kw in _BOTH_KEYWORDS):
        return "BOTH"

    has_us = any(kw in message_lower for kw in _US_KEYWORDS)
    has_kr = any(kw in message_lower for kw in _KR_KEYWORDS)

    if has_us and not has_kr:
        return "US"
    elif has_kr and not has_us:
        return "KR"
    elif has_us and has_kr:
        return "KR"
    else:
        return "BOTH"


def _detect_intent(message_lower: str) -> str:
    """Detect intent category from keywords for simple path."""
    if any(kw in message_lower for kw in _RANKING_KEYWORDS):
        return "ranking"
    if any(kw in message_lower for kw in _TECHNICAL_KEYWORDS):
        return "technical"
    if any(kw in message_lower for kw in _INVESTOR_KEYWORDS):
        return "investor"
    if any(kw in message_lower for kw in _QUANT_KEYWORDS):
        return "quant"
    if any(kw in message_lower for kw in _MARKET_KEYWORDS):
        return "market"
    if any(kw in message_lower for kw in _FILTER_KEYWORDS):
        return "filter"
    if any(kw in message_lower for kw in _ANALYSIS_KEYWORDS):
        return "analysis"
    return "query"


def _detect_data_source(message_lower: str) -> str:
    """Detect data source for simple path."""
    has_external = any(kw in message_lower for kw in _EXTERNAL_ONLY_KEYWORDS)
    has_hybrid = any(kw in message_lower for kw in _HYBRID_KEYWORDS)
    has_db = any(kw in message_lower for kw in _DB_KEYWORDS)

    if has_hybrid:
        return "hybrid"
    if has_external and has_db:
        return "hybrid"
    if has_external and not has_db:
        return "external_only"
    return "db_only"


def _detect_stock_scope(message_lower: str, has_stocks: bool) -> str:
    """Detect stock scope (specific vs broad)."""
    broad_indicators = ["상위", "하위", "top", "bottom", "순위", "랭킹",
                        "종목", "전체", "시장", "all"]
    if any(kw in message_lower for kw in broad_indicators) and not has_stocks:
        return "broad"
    return "specific"


def _detect_required_apis(message_lower: str, data_source: str) -> list:
    """Detect required external APIs."""
    if data_source == "db_only":
        return []

    required = []
    news_kw = ["뉴스", "news", "기사", "소식", "보도"]
    if any(kw in message_lower for kw in news_kw):
        required.extend(["naver", "serper"])

    analysis_kw = ["리스크", "위험", "전망", "분석", "평가", "의견"]
    if any(kw in message_lower for kw in analysis_kw):
        if "naver" not in required:
            required.append("naver")
        if "serper" not in required:
            required.append("serper")

    disclosure_kw = ["공시", "disclosure", "발표", "보고서"]
    if any(kw in message_lower for kw in disclosure_kw):
        required.append("dart")

    if not required and data_source in ["external_only", "hybrid"]:
        required = ["naver", "serper"]

    return required



def _try_prepend_stock_from_history(
    message: str,
    messages: list,
    message_lower: str,
) -> Optional[str]:
    """
    For short follow-up queries, prepend stock name from conversation history.

    Returns expanded message if applicable, None otherwise.
    """
    # Only for short messages that look like follow-ups
    if len(message) > 30:
        return None

    # Check for context-switch keywords -> should go complex
    if any(kw in message_lower for kw in _CONTEXT_SWITCH_KEYWORDS):
        return None

    if not messages:
        return None

    # Scan recent user messages for stock context
    for msg in reversed(messages[-6:]):
        if not isinstance(msg, HumanMessage):
            continue
        content = msg.content if hasattr(msg, 'content') else ""
        if not content:
            continue

        # Try to find stock names in previous user message
        # Use simple pattern: Korean company-like words (2+ chars)
        # This is a lightweight check; actual resolution happens in entity_extractor
        korean_names = re.findall(r'([가-힣]{2,10}(?:전자|화학|바이오|제약|건설|증권|은행|금융|홀딩스|지주|에너지|솔루션))', content)
        if korean_names:
            prepended = f"{korean_names[0]} {message}"
            logger.info(f"[QueryRouter] Follow-up prepend: '{message}' -> '{prepended}'")
            return prepended

        # Check for English stock symbols in previous message
        symbols = re.findall(r'\b([A-Z]{2,5})\b', content)
        filtered = [s for s in symbols if s not in {"RSI", "MACD", "AND", "OR", "DESC", "ASC", "ETF", "TOP", "PER", "PBR", "EPS", "ROE", "ROA"}]
        if filtered:
            prepended = f"{filtered[0]} {message}"
            logger.info(f"[QueryRouter] Follow-up prepend: '{message}' -> '{prepended}'")
            return prepended

        # Check for Korean stock names (from fallback mappings)
        from .entity_extractor import STOCK_MAPPINGS_FALLBACK
        content_lower = content.lower()
        for name in STOCK_MAPPINGS_FALLBACK:
            if name.lower() in content_lower or name in content:
                prepended = f"{name} {message}"
                logger.info(f"[QueryRouter] Follow-up prepend: '{message}' -> '{prepended}'")
                return prepended

    return None


async def query_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query router with keyword-based chat/external detection.

    Routes:
      "chat"     - greetings, concept explanations (keyword rules)
      "external" - pure news/disclosure queries (keyword rules)
      "complex"  - all DB queries -> query_decomposer (default)

    Args:
        state: Current graph state with 'message' field

    Returns:
        Updated state with query_route and supporting fields
    """
    logger.info("[AlphaAI:QueryRouter] Processing...")

    message = state.get("message", "")
    messages = state.get("messages", [])
    message_lower = message.lower()
    message_len = len(message)

    # === Step 1: Chat / Explain detection (keyword rules) ===
    chat_explain = _is_chat_or_explain(message_lower, message_len)
    if chat_explain:
        route = "chat"
        intent = chat_explain  # "chat" or "explain"
        logger.info(f"[AlphaAI:QueryRouter] Route: {route}, Intent: {intent}")
        return {
            **state,
            "query_route": route,
            "intent": intent,
            "market": "KR",
            "data_source": "db_only",
            "processing_steps": state.get("processing_steps", []) + ["query_router"],
        }

    # === Step 2: External-only detection (keyword rules) ===
    if _is_external_only(message_lower):
        route = "external"
        market = _detect_market(message_lower)
        data_source = "external_only"
        required_apis = _detect_required_apis(message_lower, data_source)

        logger.info(f"[AlphaAI:QueryRouter] Route: {route}, Market: {market}")
        return {
            **state,
            "query_route": route,
            "intent": "query",
            "market": market,
            "data_source": data_source,
            "required_apis": required_apis,
            "search_scope": "global_only" if market == "US" else "local_only",
            "processing_steps": state.get("processing_steps", []) + ["query_router"],
        }

    # === Step 3: All DB queries -> complex path ===
    route = "complex"
    market = _detect_market(message_lower)

    logger.info(f"[AlphaAI:QueryRouter] Route: {route}, Market: {market}")

    return {
        **state,
        "query_route": route,
        "market": market,
        "processing_steps": state.get("processing_steps", []) + ["query_router"],
    }
