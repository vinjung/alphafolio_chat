# services/chat/alpha_ai_model/graph/nodes/intent_classifier.py
"""
Intent Classification Node

Classifies user intent using LLM into categories:
- query: Simple data lookup (single stock info)
- ranking: Top N items by some criteria
- filter: Condition-based filtering
- technical: Technical indicator analysis
- investor: Investor trading flow analysis
- quant: Quant grade/score analysis
- market: Market index queries
- analysis: Complex analysis request
"""
from typing import Dict, Any
from config import logger
from core.llm.factory import get_llm, LLMProvider


# Intent classification prompt
INTENT_CLASSIFICATION_PROMPT = """Classify the user's question into one of the following categories.

Categories:
- chat: General conversation, greetings, test messages, date/time questions, basic calculations,
        or questions NOT related to stocks/finance
        (e.g., "Hello", "오늘 몇일이야?", "안녕", "100+200은?", "테스트")
- explain: Financial/investment concept explanations that don't require specific stock data
        (e.g., "RSI가 뭐야?", "PER 설명해줘", "볼린저밴드란?", "시가총액이 뭐야?", "공매도가 뭐야?")
- query: Simple lookup for a specific stock (e.g., "Samsung stock price", "Apple current price")
- ranking: Top N items by criteria (e.g., "Top 10 by trading volume", "Highest market cap stocks")
- filter: Filtering by conditions (e.g., "Stocks above 1 trillion market cap", "RSI below 30")
- technical: Technical indicator analysis (e.g., "Golden cross stocks", "Bollinger band breakout")
- investor: Investor trading flow (e.g., "Foreign net buying", "Institutional selling")
- quant: Quant grades/scores (e.g., "A-grade stocks", "Value score top 10")
- market: Market index queries (e.g., "KOSPI index", "NASDAQ today")
- analysis: Complex multi-factor analysis

IMPORTANT classification rules:
- If the question asks "what is X?" or "explain X" about a financial term -> explain
- If the question asks for specific stock data -> query/ranking/filter/technical/etc.
- If the question is general conversation or unrelated to finance -> chat

Also determine the market:
- KR: Korean stocks. Classify as KR if ANY of these conditions:
  * Mentions Korean companies (Samsung, Hyundai, SK, LG, Naver, Kakao, etc.)
  * Mentions Korean exchanges (KOSPI, KOSDAQ, KONEX)
  * Asks about KR-specific data that doesn't exist in US market:
    - Investor type trading (외국인, 기관, 개인, 순매수, 순매도) - US has NO investor type data
    - Program trading (프로그램 매매) - US has NO program trading data
    - Foreign ownership rate (외국인 지분율) - US has NO foreign ownership data
    - Block trades (대량매매) - US has NO block trade data
    - DART data (최대주주, 자사주, 임원정보) - US has NO DART data
    - Research reports (증권사 리포트, 목표주가) - US has NO research report data

- US: US stocks. Classify as US if ANY of these conditions:
  * Mentions US companies (Apple, Tesla, Google, Amazon, Microsoft, Nvidia, etc.)
  * Mentions US exchanges (NASDAQ, NYSE, S&P, Dow)
  * Asks about US-specific data that doesn't exist in KR market:
    - OPTIONS data (옵션, 콜옵션, 풋옵션, 풋콜비율, put/call ratio, IV, delta, gamma, GEX)
    - VIX (VIX, 빅스, 공포지수, 변동성지수)
    - INSIDER transactions (내부자 거래, 내부자 매수/매도)
    - US MACRO data (연방기금금리, fed funds, 국채수익률, treasury yield, 미국 CPI/GDP/PMI)
    - Market indicators (달러인덱스, DXY, 크레딧 스프레드, MOVE index, 역레포)

- BOTH: Query applies to both markets. Classify as BOTH if:
  * Explicitly mentions both markets: 한미, 한국과 미국, 양국, both markets, KR+US
  * Uses common indicators/conditions that exist in both markets (RSI, MACD, VWAP, volume, etc.)
  * No market-specific keywords are mentioned
  * Examples: "한미 반도체 관련주", "한국과 미국 반도체 비교", "RSI 30 이하 종목", "거래량 급등 종목"

IMPORTANT context rules:
- If conversation history is provided, use it to understand the context of the current question
- If the current question is a follow-up about a previously mentioned stock/topic, classify based on the combined context
- Example: If history mentions "Samsung stock price" and current question is "RSI trend?", classify as technical/KR (not chat/BOTH)
- The most recent explicit stock/market reference in history should inform the market classification

{conversation_context}

User Question: {question}

Also determine the stock scope:
- specific: The question asks about specific stocks or needs a particular stock context to answer
  (e.g., "삼성전자 현재가", "RSI 분석해줘" when a stock was mentioned before, "이 종목 차트 보여줘")
- broad: The question searches/discovers/ranks across all stocks without needing a specific stock context
  (e.g., "거래대금 상위 10개", "RSI 30 이하 종목", "애널리스트 리포트가 긍정적인 종목 TOP10")

## Follow-up Detection
Determine if this query depends on conversation context:
- true: Query references previous discussion and cannot be understood alone (e.g., "RSI 알려줘" after stock mention, "차트 보여줘" after discussing a stock, "그럼 MACD는?")
- false: Query is self-contained and can be answered independently (e.g., "배당수익률 높은 미국 주식 10개 찾아줘", "오늘 시장 어때?", "삼성전자 현재가")

Respond in this exact format:
INTENT: <category>
MARKET: <KR, US, or BOTH>
STOCK_SCOPE: <specific or broad>
IS_FOLLOW_UP: <true or false>
"""


async def classify_with_llm(
    message: str,
    provider: str = None,
    model: str = None,
    conversation_context: str = ""
) -> Dict[str, str]:
    """
    Classify intent using LLM

    Args:
        message: User's question
        provider: LLM provider
        model: Model name
        conversation_context: Recent conversation history for context

    Returns:
        Dict with 'intent' and 'market'
    """
    try:
        # Get LLM
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        # Create prompt
        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            question=message,
            conversation_context=conversation_context
        )

        # Get response
        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Parse response
        intent = "query"
        market = "KR"
        stock_scope = "specific"
        is_follow_up = False

        for line in response_text.strip().split('\n'):
            line = line.strip()
            if line.startswith("INTENT:"):
                intent = line.replace("INTENT:", "").strip().lower()
            elif line.startswith("MARKET:"):
                market = line.replace("MARKET:", "").strip().upper()
            elif line.startswith("STOCK_SCOPE:"):
                stock_scope = line.replace("STOCK_SCOPE:", "").strip().lower()
            elif line.startswith("IS_FOLLOW_UP:"):
                is_follow_up = line.replace("IS_FOLLOW_UP:", "").strip().lower() == "true"

        # Validate intent
        valid_intents = ["chat", "explain", "query", "ranking", "filter", "technical", "investor", "quant", "market", "analysis"]
        if intent not in valid_intents:
            intent = "query"

        # Validate market
        if market not in ["KR", "US", "BOTH"]:
            market = "KR"

        # Validate stock_scope
        if stock_scope not in ["specific", "broad"]:
            stock_scope = "specific"

        return {"intent": intent, "market": market, "stock_scope": stock_scope, "is_follow_up": is_follow_up}

    except Exception as e:
        logger.error(f"[IntentClassifier] LLM classification error: {e}")
        # Fallback to rule-based
        return classify_with_rules(message)


QUERY_REWRITE_PROMPT = """Rewrite the follow-up question into a self-contained question using the conversation context.

## Conversation Context
{context}

## Current Follow-up Question
{question}

## Rules
1. Combine the topic/intent from conversation context with the current question
2. Output ONLY the rewritten question, nothing else
3. Keep it concise and natural
4. Preserve the original language (Korean/English)

## Rewritten Question
"""


async def _rewrite_with_context(
    message: str,
    conversation_context: str,
    provider: str = None,
    model: str = None
) -> str:
    """
    Rewrite a short follow-up query into a self-contained question using conversation context.

    Args:
        message: Short follow-up message
        conversation_context: Recent conversation history
        provider: LLM provider
        model: Model name

    Returns:
        Rewritten self-contained question, or original message on failure
    """
    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        prompt = QUERY_REWRITE_PROMPT.format(
            context=conversation_context,
            question=message
        )

        response = await llm.ainvoke(prompt)
        rewritten = response.content if hasattr(response, 'content') else str(response)
        rewritten = rewritten.strip()

        if rewritten and len(rewritten) > len(message):
            logger.info(f"[IntentClassifier] Query rewritten: '{message}' -> '{rewritten}'")
            return rewritten

        return message

    except Exception as e:
        logger.warning(f"[IntentClassifier] Query rewrite failed: {e}")
        return message


def classify_with_rules(message: str) -> Dict[str, str]:
    """
    Rule-based intent classification (fallback)

    Args:
        message: User's question

    Returns:
        Dict with 'intent' and 'market'
    """
    message_lower = message.lower()
    intent = "query"
    market = "KR"

    # Chat intent detection (general conversation, greetings, date/time, etc.)
    chat_keywords = ["안녕", "hello", "hi", "테스트", "test", "몇일", "몇시", "날씨",
                     "고마워", "감사", "thanks", "잘가", "bye", "뭐해", "심심"]
    chat_patterns = ["오늘 ", "지금 ", "현재 시간", "몇 월", "무슨 요일"]

    # Explain intent detection (concept explanations)
    explain_patterns = ["뭐야", "뭐에요", "뭔가요", "무엇인가요", "무엇이야", "이란?", "이란",
                        "설명해", "알려줘", "what is", "explain", "이 뭐", "가 뭐", "은 뭐", "는 뭐",
                        "개념", "정의", "의미"]
    explain_terms = ["rsi", "macd", "per", "pbr", "eps", "roe", "roa", "시가총액", "거래량",
                     "볼린저", "이동평균", "골든크로스", "데드크로스", "공매도", "배당", "증거금"]

    # Check for chat intent first
    if any(kw in message_lower for kw in chat_keywords):
        return {"intent": "chat", "market": "KR"}
    if any(pattern in message_lower for pattern in chat_patterns):
        return {"intent": "chat", "market": "KR"}

    # Check for explain intent (concept explanation without specific stock)
    has_explain_pattern = any(pattern in message_lower for pattern in explain_patterns)
    has_explain_term = any(term in message_lower for term in explain_terms)
    # Check if asking about a concept without a specific stock name
    stock_name_indicators = ["주가", "현재가", "가격", "종목", "005930", "삼성전자", "애플"]
    has_stock_reference = any(ind in message_lower for ind in stock_name_indicators)

    if has_explain_pattern and has_explain_term and not has_stock_reference:
        return {"intent": "explain", "market": "KR"}
    if has_explain_pattern and not has_stock_reference and len(message) < 30:
        # Short question asking "what is X" without stock reference
        return {"intent": "explain", "market": "KR"}

    # Intent detection for stock-related queries
    ranking_keywords = ["상위", "top", "랭킹", "순위", "최고", "best", "highest", "lowest"]
    filter_keywords = ["이상", "이하", "초과", "미만", "필터", "조건", "where"]
    technical_keywords = ["rsi", "macd", "볼린저", "이평", "골든크로스", "데드크로스", "과매수", "과매도"]
    investor_keywords = ["외국인", "외인", "기관", "개인", "개미", "순매수", "순매도"]
    quant_keywords = ["등급", "grade", "점수", "score", "퀀트", "가치주", "성장주", "모멘텀"]
    market_keywords = ["코스피", "코스닥", "지수", "index", "kospi", "kosdaq"]

    if any(kw in message_lower for kw in ranking_keywords):
        intent = "ranking"
    elif any(kw in message_lower for kw in technical_keywords):
        intent = "technical"
    elif any(kw in message_lower for kw in investor_keywords):
        intent = "investor"
    elif any(kw in message_lower for kw in quant_keywords):
        intent = "quant"
    elif any(kw in message_lower for kw in market_keywords):
        intent = "market"
    elif any(kw in message_lower for kw in filter_keywords):
        intent = "filter"

    # Market detection - check US first, then KR, then BOTH
    us_keywords = [
        # Exchanges and general
        "미국", "나스닥", "nasdaq", "nyse", "s&p", "다우", "dow",
        # US companies
        "애플", "apple", "테슬라", "tesla", "구글", "google",
        "아마존", "amazon", "마이크로소프트", "microsoft", "엔비디아", "nvidia",
        # US-only data: Options (KR market has NO options data)
        "옵션", "콜옵션", "풋옵션", "풋콜비율", "put/call", "pcr",
        "내재변동성", "implied volatility", "iv ", " iv",
        "delta", "gamma", "theta", "vega", "gex", "gamma exposure",
        "미결제약정", "open interest", "행사가격", "strike",
        # US-only data: VIX (KR market has NO VIX data)
        "vix", "빅스", "공포지수", "변동성지수",
        # US-only data: Insider transactions (KR market has NO insider data)
        "내부자 거래", "내부자 매수", "내부자 매도", "insider",
        # US-only data: US Macro/Economic indicators
        "연방기금금리", "fed fund", "연준금리", "fomc",
        "국채수익률", "treasury yield", "10년물", "2년물", "장단기금리",
        "미국 cpi", "미국 물가", "미국 실업률", "미국 gdp", "미국 pmi",
        # US-only data: Market indicators
        "달러인덱스", "dxy", "달러지수",
        "크레딧 스프레드", "신용 스프레드", "하이일드",
        "move index", "move 지수", "채권변동성",
        "역레포", "reverse repo", "rrp"
    ]

    kr_keywords = [
        # Exchanges (Korean market specific)
        "코스피", "코스닥", "kospi", "kosdaq", "유가증권", "코넥스", "konex",
        # KR-only data: Investor trading (US market has NO investor type data)
        "외국인", "외인", "기관", "개인", "개미",
        "순매수", "순매도", "외인 순매수", "기관 순매수", "개인 순매수",
        "외국인 매수", "외국인 매도", "기관 매수", "기관 매도",
        "투자자별", "투자주체",
        # KR-only data: Program trading
        "프로그램", "프로그램 매매", "프로그램 순매수", "프로그램 순매도",
        "차익거래", "비차익거래",
        # KR-only data: Block trades
        "대량매매", "블록딜", "대량거래", "블록트레이드",
        # KR-only data: Foreign ownership rate
        "외국인 지분", "외인 지분", "외국인 한도", "외국인 보유",
        "지분율", "한도소진",
        # KR-only data: DART financial statements
        "dart", "다트", "감사보고서", "사업보고서", "분기보고서",
        # KR-only data: Largest shareholder
        "최대주주", "대주주", "지배주주", "주주구성",
        # KR-only data: Treasury stock
        "자사주", "자기주식", "자사주 매입", "자사주 소각", "자사주 처분",
        # KR-only data: Executives
        "등기임원",
        # KR-only data: Research reports
        "리서치", "목표주가", "투자의견", "증권사 리포트", "애널리스트 리포트",
        # KR-only data: Benchmark indices
        "kospi200", "kospi 200", "코스피200", "krx100", "krx 100",
        "kosdaq150", "섹터지수",
        # Korean company names (major)
        "삼성전자", "삼성", "현대", "네이버", "카카오",
        "셀트리온", "삼성바이오", "현대차", "기아", "포스코", "kb금융",
        "신한지주", "하나금융", "삼성sdi", "lg에너지", "lg화학"
    ]

    # Check for explicit BOTH-market keywords first
    both_keywords = ["한미", "양국", "한국과 미국", "한국 미국"]
    if any(kw in message_lower for kw in both_keywords):
        return {"intent": intent, "market": "BOTH"}

    # Check for US-specific keywords first
    has_us_keyword = any(kw in message_lower for kw in us_keywords)
    # Check for KR-specific keywords
    has_kr_keyword = any(kw in message_lower for kw in kr_keywords)

    if has_us_keyword and not has_kr_keyword:
        market = "US"
    elif has_kr_keyword and not has_us_keyword:
        market = "KR"
    elif has_us_keyword and has_kr_keyword:
        # Both keywords present - default to KR (user likely comparing)
        market = "KR"
    else:
        # Neither US nor KR specific keywords - use BOTH markets
        market = "BOTH"

    return {"intent": intent, "market": market}


async def intent_classifier(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify user intent from natural language query

    Args:
        state: Current graph state with 'message' field

    Returns:
        Updated state with 'intent' and 'market' fields
    """
    logger.info("[AlphaAI:IntentClassifier] Processing...")

    message = state.get("message", "")
    provider = state.get("provider")
    model = state.get("model_name")

    # Build conversation context from recent messages
    conversation_context = ""
    messages = state.get("messages", [])
    if messages:
        from langchain_core.messages import HumanMessage
        context_lines = []
        # Use last few messages for context (max 6 messages = 3 turns)
        recent_messages = messages[-6:]
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                context_lines.append(f"User: {msg.content}")
            else:
                # AIMessage - include brief summary only
                content = msg.content if hasattr(msg, 'content') else str(msg)
                if len(content) > 100:
                    content = content[:100] + "..."
                context_lines.append(f"Assistant: {content}")
        if context_lines:
            conversation_context = "\n".join(context_lines)

    # Try LLM classification, fallback to rules
    try:
        result = await classify_with_llm(message, provider, model, conversation_context)
    except Exception as e:
        logger.warning(f"[IntentClassifier] LLM failed, using rules: {e}")
        result = classify_with_rules(message)

    intent = result["intent"]
    market = result["market"]
    stock_scope = result.get("stock_scope", "specific")
    is_follow_up = result.get("is_follow_up", False)

    # Follow-up query rewriting: expand follow-up queries with conversation context (LLM-based detection)
    expanded_message = None
    if conversation_context and is_follow_up:
        expanded_message = await _rewrite_with_context(
            message, conversation_context, provider, model
        )
        # If rewrite returned the same message, don't set expanded_message
        if expanded_message == message:
            expanded_message = None

    logger.info(f"[AlphaAI:IntentClassifier] Intent: {intent}, Market: {market}, "
                f"StockScope: {stock_scope}"
                f"{f', Expanded: {expanded_message}' if expanded_message else ''}")

    return {
        **state,
        "intent": intent,
        "market": market,
        "stock_scope": stock_scope,
        **({"expanded_message": expanded_message} if expanded_message else {}),
        "processing_steps": state.get("processing_steps", []) + ["intent_classifier"]
    }
