# services/chat/alpha_ai_model/graph/nodes/entity_extractor.py
"""
Entity Extraction Node

Extracts entities from user query using LLM and rule-based parsing:
- Stock names and codes (via StockResolver)
- Technical indicators
- Conditions and thresholds
- Time ranges
- Sorting and limit parameters
"""
from typing import Dict, Any, List, Optional
import re
from config import logger
from core.llm.factory import get_llm, LLMProvider

from langchain_core.messages import HumanMessage, AIMessage

from ...rag import SelfQueryRetriever, QueryExpander
from ...stock_resolver import StockResolver, Market

# Only accept high-confidence match methods from StockResolver
# Rejects fuzzy matches that cause false positives (e.g., "현금흐름" -> random stock)
ACCEPTED_MATCH_METHODS = {"exact", "alias", "partial"}

# For AI response fallback, only accept exact matches to prevent false positives
# (e.g., "감성" in AI response text -> 감성코퍼레이션 via partial match)
AI_RESPONSE_MATCH_METHODS = {"exact"}


# LLM extraction prompt
ENTITY_EXTRACTION_PROMPT = """Extract entities from the following stock market query.

Query: {query}

Extract entities in this exact JSON format:
{{
    "stock_names": ["list of stock names mentioned"],
    "stock_codes": ["list of stock codes if mentioned"],
    "indicators": ["list of technical indicators: rsi, macd, bollinger, etc."],
    "conditions": {{
        "column_name": {{"op": ">=|<=|>|<|=", "value": number}}
    }},
    "time_range": {{"start": "YYYY-MM-DD or null", "end": "YYYY-MM-DD or null", "period": "1d|5d|1m|3m|etc"}},
    "limit": number or null,
    "order_by": "column_name or null",
    "order_direction": "ASC|DESC or null"
}}

Examples:
- "삼성전자 현재가" -> stock_names: ["삼성전자"]
- "RSI 30 이하" -> indicators: ["rsi"], conditions: {{"rsi": {{"op": "<=", "value": 30}}}}
- "거래대금 상위 10개" -> order_by: "trading_value", order_direction: "DESC", limit: 10
- "시총 1조 이상" -> conditions: {{"market_cap": {{"op": ">=", "value": 1000000000000}}}}

Output only valid JSON:"""


# Stock name to code mapping (FALLBACK - used when StockResolver is not available)
# Primary stock resolution now uses StockResolver with database lookup
STOCK_MAPPINGS_FALLBACK = {
    # Korean stocks
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "LG에너지솔루션": "373220",
    "삼성바이오로직스": "207940",
    "현대차": "005380",
    "기아": "000270",
    "셀트리온": "068270",
    "KB금융": "105560",
    "신한지주": "055550",
    "POSCO홀딩스": "005490",
    "네이버": "035420",
    "카카오": "035720",
    "삼성SDI": "006400",
    "LG화학": "051910",
    "현대모비스": "012330",

    # US stocks (Korean names)
    "애플": "AAPL",
    "테슬라": "TSLA",
    "엔비디아": "NVDA",
    "마이크로소프트": "MSFT",
    "아마존": "AMZN",
    "구글": "GOOGL",
    "알파벳": "GOOGL",
    "메타": "META",
    "페이스북": "META",
}


# Common non-stock Korean words to exclude from stock candidate extraction
NON_STOCK_WORDS = {
    # Financial terms
    '현재가', '주가', '거래량', '시가총액', '등락률', '상위', '하위',
    '이상', '이하', '최근', '오늘', '어제', '이번', '지난',
    # Common verbs/adjectives/adverbs
    '분석', '설명', '알려', '보여', '확인', '비교', '정렬', '검색',
    '봐야', '해야', '뭔지', '어떤', '얼마', '전망', '예측',
    '분석하고', '분석해줘', '알려줘', '보여줘', '확인해줘', '비교해줘',
    # Common nouns not stock-related
    '지표', '종목', '차트', '그래프', '데이터', '결과', '기간',
    '방법', '이유', '요인', '리스크', '전략', '매매', '투자',
    '상승', '하락', '추세', '추이', '변화', '흐름', '동향',
    '시장', '업종', '섹터', '산업', '경제', '금리', '환율',
    # Common adverbs/pronouns/particles that trigger false positive partial matches
    '모두', '각각', '우리', '서로', '함께', '직접', '자체',
    '아직', '이미', '매우', '위해', '대한', '사이', '통한',
    '중에서', '가운데', '전체', '해당', '감안', '선별',
    '비교해서', '정렬해', '기준으로',
}


def extract_stock_candidates(message: str) -> List[str]:
    """
    Extract potential stock name candidates from message

    Uses various patterns to identify potential stock names:
    - Korean company names (ending with specific suffixes)
    - English company names
    - Direct symbol patterns

    Args:
        message: User message

    Returns:
        List of potential stock name candidates
    """
    candidates = []

    # Pattern 1: Korean stock names (common patterns)
    # Match sequences of Korean characters that look like company names
    korean_patterns = [
        r'([가-힣]+(?:전자|화학|바이오|제약|건설|증권|은행|보험|카드|금융|홀딩스|지주|모비스|에너지|솔루션))',
        r'([가-힣]{2,10})',  # General Korean words (2-10 chars)
    ]

    for pattern in korean_patterns:
        matches = re.findall(pattern, message)
        for match in matches:
            if match and len(match) >= 2 and match not in candidates:
                # Filter out common non-stock words
                if match not in NON_STOCK_WORDS:
                    candidates.append(match)

    # Pattern 2: English company names (capitalized words)
    english_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b'
    english_matches = re.findall(english_pattern, message)
    for match in english_matches:
        if match not in ['RSI', 'MACD', 'AND', 'OR', 'DESC', 'ASC'] and match not in candidates:
            candidates.append(match)

    # Pattern 3: Stock symbols (all caps, 2-5 letters)
    symbol_pattern = r'\b([A-Z]{2,5})\b'
    symbol_matches = re.findall(symbol_pattern, message)
    for match in symbol_matches:
        if match not in ['RSI', 'MACD', 'AND', 'OR', 'DESC', 'ASC', 'ETF'] and match not in candidates:
            candidates.append(match)

    # Pattern 4: Korean stock codes (6 digits)
    kr_code_pattern = r'\b(\d{6})\b'
    kr_codes = re.findall(kr_code_pattern, message)
    candidates.extend(kr_codes)

    return candidates


async def resolve_stocks_from_message(
    message: str,
    market_hint: Optional[str] = None,
    accepted_methods: set = None
) -> Dict[str, Any]:
    """
    Resolve stock names from message using StockResolver

    Args:
        message: User message
        market_hint: Market hint (KR/US)
        accepted_methods: Set of accepted match methods (default: ACCEPTED_MATCH_METHODS)

    Returns:
        Dictionary with stock_names, stock_codes, stock_info
    """
    result = {
        "stock_names": [],
        "stock_codes": [],
        "stock_info": []  # Detailed match info
    }

    # Get StockResolver instance
    resolver = StockResolver.get_instance()

    # Convert market hint to Market enum
    market = None
    if market_hint == "KR":
        market = Market.KR
    elif market_hint == "US":
        market = Market.US

    # Extract candidates
    candidates = extract_stock_candidates(message)

    if not candidates:
        return result

    # Resolve each candidate
    methods = accepted_methods or ACCEPTED_MATCH_METHODS
    resolved_symbols = set()  # Track resolved symbols to avoid duplicates

    for candidate in candidates:
        try:
            match_result = await resolver.resolve(candidate, market)

            if match_result and match_result.method in methods and match_result.stock.symbol not in resolved_symbols:
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
                    "matched_term": match_result.matched_term
                })

                logger.debug(f"[EntityExtractor] Resolved: '{candidate}' -> "
                           f"{match_result.stock.symbol} ({match_result.method}, "
                           f"conf={match_result.confidence:.2f})")

        except Exception as e:
            logger.warning(f"[EntityExtractor] Failed to resolve '{candidate}': {e}")

    return result


# Global instances
_self_query: SelfQueryRetriever = None
_query_expander: QueryExpander = None


def get_self_query() -> SelfQueryRetriever:
    """Get or initialize SelfQueryRetriever"""
    global _self_query
    if _self_query is None:
        _self_query = SelfQueryRetriever(use_llm=False)  # Use rule-based only
    return _self_query


def get_query_expander() -> QueryExpander:
    """Get or initialize QueryExpander"""
    global _query_expander
    if _query_expander is None:
        _query_expander = QueryExpander(use_llm=False)  # Use rule-based only
    return _query_expander


async def extract_with_llm(
    message: str,
    provider: str = None,
    model: str = None
) -> Dict[str, Any]:
    """
    Extract entities using LLM

    Args:
        message: User message
        provider: LLM provider
        model: Model name

    Returns:
        Extracted entities dictionary
    """
    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        prompt = ENTITY_EXTRACTION_PROMPT.format(query=message)
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)

        # Parse JSON from response
        import json
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
            return result

        return {}

    except Exception as e:
        logger.warning(f"[EntityExtractor] LLM extraction failed: {e}")
        return {}


def extract_with_rules(message: str, market: str = "KR") -> Dict[str, Any]:
    """
    Extract entities using rule-based patterns

    Args:
        message: User message
        market: Market (KR/US)

    Returns:
        Extracted entities dictionary
    """
    entities = {
        "stock_names": [],
        "stock_codes": [],
        "indicators": [],
        "conditions": {},
        "time_range": None,
        "limit": None,
        "order_by": None,
        "order_direction": None
    }

    message_lower = message.lower()

    # Extract stock names using fallback mappings
    # Note: Primary stock resolution uses StockResolver in entity_extractor()
    for name, code in STOCK_MAPPINGS_FALLBACK.items():
        if name.lower() in message_lower or name in message:
            entities["stock_names"].append(name)
            entities["stock_codes"].append(code)

    # Extract stock codes directly (Korean: 6 digits, US: letters)
    kr_codes = re.findall(r'\b(\d{6})\b', message)
    for code in kr_codes:
        if code not in entities["stock_codes"]:
            entities["stock_codes"].append(code)

    us_codes = re.findall(r'\b([A-Z]{2,5})\b', message)
    for code in us_codes:
        if code not in entities["stock_codes"] and code not in ["RSI", "MACD", "AND", "OR"]:
            entities["stock_codes"].append(code)

    # Extract indicators
    indicator_patterns = {
        "rsi": [r'rsi', r'알에스아이', r'상대강도'],
        "macd": [r'macd', r'맥디'],
        "bollinger": [r'볼린저', r'bb', r'bollinger'],
        "ma": [r'이평', r'이동평균', r'ma\d+'],
        "vwap": [r'vwap', r'거래량가중'],
        "stochastic": [r'스토캐스틱', r'stoch'],
    }

    for indicator, patterns in indicator_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                if indicator not in entities["indicators"]:
                    entities["indicators"].append(indicator)
                break

    # Extract limit
    limit_match = re.search(r'(상위|하위|top|bottom)\s*(\d+)', message_lower)
    if limit_match:
        entities["limit"] = int(limit_match.group(2))
        entities["order_direction"] = "DESC" if limit_match.group(1) in ["상위", "top"] else "ASC"

    limit_match2 = re.search(r'(\d+)\s*(개|종목)', message_lower)
    if limit_match2 and not entities["limit"]:
        entities["limit"] = int(limit_match2.group(1))

    # Extract order_by
    order_keywords = {
        "거래대금": "trading_value",
        "거래량": "volume",
        "시총": "market_cap",
        "시가총액": "market_cap",
        "등락률": "change_rate",
        "변동률": "change_rate",
        "rsi": "rsi",
    }

    for keyword, column in order_keywords.items():
        if keyword in message_lower and ("상위" in message_lower or "하위" in message_lower):
            entities["order_by"] = column
            break

    # Extract conditions using SelfQueryRetriever
    self_query = get_self_query()
    filters = self_query._extract_filters_rule_based(message)

    for f in filters:
        entities["conditions"][f.column] = {
            "op": f.operator.value,
            "value": f.value
        }

    # Extract time range
    time_patterns = [
        (r'오늘', {"period": "1d"}),
        (r'이번\s*주', {"period": "1w"}),
        (r'이번\s*달', {"period": "1m"}),
        (r'최근\s*(\d+)\s*일', lambda m: {"period": f"{m.group(1)}d"}),
        (r'최근\s*(\d+)\s*개월', lambda m: {"period": f"{m.group(1)}m"}),
    ]

    for pattern, result in time_patterns:
        match = re.search(pattern, message_lower)
        if match:
            if callable(result):
                entities["time_range"] = result(match)
            else:
                entities["time_range"] = result
            break

    return entities


def _group_messages_into_turns(messages) -> list:
    """
    Group message list into (user_content, ai_content) turn pairs.
    state["messages"] is ordered [HumanMessage, AIMessage, HumanMessage, AIMessage, ...].

    Returns:
        List of (user_content, ai_content) tuples
    """
    turns = []
    i = 0
    while i < len(messages):
        user_content = None
        ai_content = None

        if isinstance(messages[i], HumanMessage):
            user_content = messages[i].content if hasattr(messages[i], 'content') else ""
            # Pair with next AIMessage if available
            if i + 1 < len(messages) and isinstance(messages[i + 1], AIMessage):
                ai_content = messages[i + 1].content if hasattr(messages[i + 1], 'content') else ""
                i += 2
            else:
                i += 1
        elif isinstance(messages[i], AIMessage):
            ai_content = messages[i].content if hasattr(messages[i], 'content') else ""
            i += 1
        else:
            i += 1
            continue

        if user_content or ai_content:
            turns.append((user_content or "", ai_content or ""))

    return turns


async def entity_extractor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract entities from natural language query

    Uses StockResolver for stock name resolution, plus LLM and rule-based
    extraction for other entities.

    Args:
        state: Current graph state with 'message' field

    Returns:
        Updated state with 'entities' field
    """
    logger.info("[AlphaAI:EntityExtractor] Processing...")

    message = state.get("message", "")
    market = state.get("market", "KR")
    provider = state.get("provider")
    model = state.get("model_name")

    # Rule-based extraction for non-stock entities (fast)
    entities = extract_with_rules(message, market)

    # Stock resolution using StockResolver (primary method)
    try:
        stock_result = await resolve_stocks_from_message(message, market)

        # Use StockResolver results if found
        if stock_result["stock_codes"]:
            entities["stock_names"] = stock_result["stock_names"]
            entities["stock_codes"] = stock_result["stock_codes"]
            entities["stock_info"] = stock_result["stock_info"]
            logger.info(f"[EntityExtractor] StockResolver found {len(stock_result['stock_codes'])} stocks")
        else:
            # Fallback to rule-based if StockResolver found nothing
            entities["stock_info"] = []
            logger.debug("[EntityExtractor] StockResolver found no stocks, using fallback")

    except Exception as e:
        logger.warning(f"[EntityExtractor] StockResolver failed, using fallback: {e}")
        entities["stock_info"] = []

    # Fallback: resolve stock from conversation history if current message has no stocks
    if not entities.get("stock_codes"):
        stock_scope = state.get("stock_scope", "specific")
        conversation_messages = state.get("messages", [])

        if stock_scope == "broad":
            # Broad scope queries (ranking/filter across all stocks) don't need specific stock context
            logger.info("[EntityExtractor] Broad scope query - skipping stock fallback")
        elif not conversation_messages:
            # First message in session with no stock -> guide flag
            entities["stock_fallback_guide"] = True
            logger.info("[EntityExtractor] No stocks found, no history -> setting fallback guide")
        else:
            # Group messages into (user, ai) turns and search recent turns
            turns = _group_messages_into_turns(conversation_messages)
            found = False

            for turn in reversed(turns[-3:]):
                user_content, ai_content = turn

                # Search user message first
                if user_content:
                    try:
                        history_stock = await resolve_stocks_from_message(user_content, market)
                        if history_stock["stock_codes"]:
                            entities["stock_names"] = history_stock["stock_names"]
                            entities["stock_codes"] = history_stock["stock_codes"]
                            entities["stock_info"] = history_stock["stock_info"]
                            logger.info(f"[EntityExtractor] Fallback from user turn: "
                                        f"{history_stock['stock_names']}")
                            found = True
                            break
                    except Exception as e:
                        logger.debug(f"[EntityExtractor] History user resolution failed: {e}")

                # If not found in user message, search AI response (exact match only)
                if ai_content:
                    try:
                        history_stock = await resolve_stocks_from_message(
                            ai_content, market, accepted_methods=AI_RESPONSE_MATCH_METHODS
                        )
                        if history_stock["stock_codes"]:
                            entities["stock_names"] = history_stock["stock_names"]
                            entities["stock_codes"] = history_stock["stock_codes"]
                            entities["stock_info"] = history_stock["stock_info"]
                            logger.info(f"[EntityExtractor] Fallback from AI turn (exact only): "
                                        f"{history_stock['stock_names']}")
                            found = True
                            break
                    except Exception as e:
                        logger.debug(f"[EntityExtractor] History AI resolution failed: {e}")

            if not found:
                entities["stock_fallback_guide"] = True
                logger.info("[EntityExtractor] No stocks found in 3 recent turns -> setting fallback guide")

    # LLM extraction for additional details
    try:
        llm_entities = await extract_with_llm(message, provider, model)

        # Merge LLM results (LLM supplements existing results)
        if llm_entities:
            # Merge stock names from LLM (only if not already found)
            if llm_entities.get("stock_names") and not entities.get("stock_codes"):
                for name in llm_entities["stock_names"]:
                    if name not in entities["stock_names"]:
                        entities["stock_names"].append(name)
                        # Try to resolve via StockResolver
                        try:
                            resolver = StockResolver.get_instance()
                            match = await resolver.resolve(name)
                            if match:
                                entities["stock_codes"].append(match.stock.symbol)
                        except Exception:
                            pass

            # Merge indicators
            if llm_entities.get("indicators"):
                for ind in llm_entities["indicators"]:
                    if ind not in entities["indicators"]:
                        entities["indicators"].append(ind)

            # Merge conditions
            if llm_entities.get("conditions"):
                for col, cond in llm_entities["conditions"].items():
                    if col not in entities["conditions"]:
                        entities["conditions"][col] = cond

            # Use LLM values if rule-based didn't find them
            if llm_entities.get("limit") and not entities["limit"]:
                entities["limit"] = llm_entities["limit"]
            if llm_entities.get("order_by") and not entities["order_by"]:
                entities["order_by"] = llm_entities["order_by"]
            if llm_entities.get("order_direction") and not entities["order_direction"]:
                entities["order_direction"] = llm_entities["order_direction"]
            if llm_entities.get("time_range") and not entities["time_range"]:
                entities["time_range"] = llm_entities["time_range"]

    except Exception as e:
        logger.warning(f"[EntityExtractor] LLM extraction failed, using rules only: {e}")

    # Query expansion for better retrieval
    query_expander = get_query_expander()
    expansion = await query_expander.expand(message, use_synonyms=True, use_rewrite=False)
    entities["keywords"] = expansion.get("keywords", [])
    entities["expanded_queries"] = expansion.get("expanded", [message])

    logger.info(f"[AlphaAI:EntityExtractor] Extracted: stocks={len(entities.get('stock_names', []))}, "
                f"indicators={len(entities['indicators'])}, conditions={len(entities['conditions'])}")

    return {
        **state,
        "entities": entities,
        "processing_steps": state.get("processing_steps", []) + ["entity_extractor"]
    }
