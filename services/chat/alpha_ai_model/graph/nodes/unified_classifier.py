# services/chat/alpha_ai_model/graph/nodes/unified_classifier.py
"""
Unified Classifier Node

Merges intent classification and entity extraction into a single LLM call.
Reduces LLM calls from 2-3 (intent + optional rewrite + entity) to 1.

Feature flag: USE_UNIFIED_CLASSIFIER (default: False)
When False, the original intent_classifier + entity_extractor nodes are used.
"""
from typing import Dict, Any, List, Optional
import re
import json as json_module
from config import logger
from core.llm.factory import get_llm, LLMProvider

from langchain_core.messages import HumanMessage, AIMessage

from ...rag import SelfQueryRetriever, QueryExpander
from ...stock_resolver import StockResolver, Market


# Accepted match methods for StockResolver (same as entity_extractor)
ACCEPTED_MATCH_METHODS = {"exact", "alias", "partial"}
AI_RESPONSE_MATCH_METHODS = {"exact"}


UNIFIED_CLASSIFICATION_PROMPT = """You are a stock market query analyzer. Analyze the following query and provide both intent classification and entity extraction in a single response.

## Part 1: Intent Classification
Classify the user's question into one of the following categories:
- chat: General conversation, greetings, test messages, date/time questions, basic calculations, or questions NOT related to stocks/finance
- explain: Financial/investment concept explanations that don't require specific stock data
- query: Simple lookup for a specific stock
- ranking: Top N items by criteria
- filter: Filtering by conditions
- technical: Technical indicator analysis
- investor: Investor trading flow analysis
- quant: Quant grades/scores analysis
- market: Market index queries
- analysis: Complex multi-factor analysis

Market determination:
- KR: Korean stocks (Korean companies, KOSPI/KOSDAQ, investor trading, program trading, foreign ownership, DART data, research reports)
- US: US stocks (US companies, NASDAQ/NYSE, options data, VIX, insider transactions, US macro data, market indicators like DXY)
- BOTH: Both markets (explicitly mentions both, or uses common indicators without market-specific keywords)

Stock scope:
- specific: Asks about specific stocks or needs a particular stock context
- broad: Searches/ranks across all stocks without needing a specific stock

## Part 2: Entity Extraction
Extract entities from the query in JSON format:
- stock_names: List of stock names mentioned (Korean or English)
- stock_codes: List of stock codes/symbols if mentioned (e.g., "005930", "AAPL")
- indicators: Technical indicators (rsi, macd, bollinger, ma, vwap, stochastic, etc.)
- conditions: Column conditions with operator and value (e.g., {{"market_cap": {{"op": ">=", "value": 1000000000000}}}})
- time_range: Time period ({{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "period": "1d|5d|1m|3m|etc"}}) or null
- limit: Number of results requested or null
- order_by: Sorting column or null
- order_direction: ASC or DESC or null

## Follow-up Detection
Determine if this query depends on conversation context:
- true: Query references previous discussion and cannot be understood alone (e.g., "RSI 알려줘" after stock mention, "차트 보여줘" after discussing a stock, "그럼 MACD는?")
- false: Query is self-contained and can be answered independently (e.g., "배당수익률 높은 미국 주식 10개 찾아줘", "오늘 시장 어때?", "삼성전자 현재가")

If IS_FOLLOW_UP is true, rewrite the query as a self-contained question using the conversation context.

{conversation_context}

User Question: {question}

Respond in this EXACT format (no extra text before or after):
INTENT: <category>
MARKET: <KR, US, or BOTH>
STOCK_SCOPE: <specific or broad>
IS_FOLLOW_UP: <true or false>
REWRITTEN_QUERY: <rewritten self-contained query if IS_FOLLOW_UP=true, otherwise NONE>
ENTITIES:
{{"stock_names": [], "stock_codes": [], "indicators": [], "conditions": {{}}, "time_range": null, "limit": null, "order_by": null, "order_direction": null}}"""


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
    market_hint: Optional[str] = None
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

    resolved_symbols = set()
    for candidate in candidates:
        try:
            match_result = await resolver.resolve(candidate, market)
            if (match_result
                    and match_result.method in ACCEPTED_MATCH_METHODS
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
            logger.warning(f"[UnifiedClassifier] Failed to resolve '{candidate}': {e}")

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


def _get_self_query() -> SelfQueryRetriever:
    """Get SelfQueryRetriever instance (reuse entity_extractor's singleton)."""
    from .entity_extractor import get_self_query
    return get_self_query()


def _get_query_expander() -> QueryExpander:
    """Get QueryExpander instance (reuse entity_extractor's singleton)."""
    from .entity_extractor import get_query_expander
    return get_query_expander()


async def unified_classifier(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unified intent classification + entity extraction node.

    Single LLM call replaces separate intent_classifier and entity_extractor nodes.
    Reduces per-request LLM calls from 2-3 to 1 (for non-follow-up queries).

    Args:
        state: Current graph state with 'message' field

    Returns:
        Updated state with 'intent', 'market', 'stock_scope', and 'entities' fields
    """
    logger.info("[AlphaAI:UnifiedClassifier] Processing...")

    message = state.get("message", "")
    provider = state.get("provider")
    model = state.get("model_name")
    messages = state.get("messages", [])

    # Build conversation context
    conversation_context = _build_conversation_context(messages)

    # === Single LLM Call (replaces intent_classifier + entity_extractor LLM calls) ===
    intent = "query"
    market = "KR"
    stock_scope = "specific"
    llm_entities = {}
    expanded_message = None

    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        prompt = UNIFIED_CLASSIFICATION_PROMPT.format(
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
            elif line.startswith("IS_FOLLOW_UP:"):
                is_follow_up = line.replace("IS_FOLLOW_UP:", "").strip().lower() == "true"
            elif line.startswith("REWRITTEN_QUERY:"):
                rewritten = line.replace("REWRITTEN_QUERY:", "").strip()
                if rewritten and rewritten.upper() != "NONE" and is_follow_up and len(rewritten) > len(message):
                    expanded_message = rewritten
                    logger.info(
                        f"[UnifiedClassifier] Query rewritten: '{message}' -> '{expanded_message}'"
                    )

        # Parse ENTITIES JSON block
        json_match = re.search(r'ENTITIES:\s*\n?\s*(\{[\s\S]*\})', response_text)
        if json_match:
            try:
                llm_entities = json_module.loads(json_match.group(1))
            except json_module.JSONDecodeError:
                logger.warning("[UnifiedClassifier] Failed to parse entities JSON from LLM")

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

    except Exception as e:
        logger.error(f"[UnifiedClassifier] LLM call failed, using rule-based fallback: {e}")
        from .intent_classifier import classify_with_rules
        rule_result = classify_with_rules(message)
        intent = rule_result["intent"]
        market = rule_result["market"]

    # === Build entities dict (merge LLM + rule-based results) ===
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
        self_query = _get_self_query()
        rule_filters = self_query._extract_filters_rule_based(message)
        for f in rule_filters:
            if f.column not in entities["conditions"]:
                entities["conditions"][f.column] = {
                    "op": f.operator.value,
                    "value": f.value,
                }
    except Exception as e:
        logger.debug(f"[UnifiedClassifier] Rule-based filter extraction failed: {e}")

    # === Stock Resolution using StockResolver (DB-based, not LLM) ===
    try:
        stock_result = await _resolve_stocks(message, market)
        if stock_result["stock_codes"]:
            entities["stock_names"] = stock_result["stock_names"]
            entities["stock_codes"] = stock_result["stock_codes"]
            entities["stock_info"] = stock_result["stock_info"]
            logger.info(
                f"[UnifiedClassifier] StockResolver found "
                f"{len(stock_result['stock_codes'])} stocks"
            )
        else:
            entities["stock_info"] = []
    except Exception as e:
        logger.warning(f"[UnifiedClassifier] StockResolver failed: {e}")
        entities["stock_info"] = []

    # === Fallback: resolve stock from conversation history ===
    if not entities.get("stock_codes"):
        if stock_scope == "broad":
            logger.info("[UnifiedClassifier] Broad scope query - skipping stock fallback")
        elif not messages:
            entities["stock_fallback_guide"] = True
            logger.info(
                "[UnifiedClassifier] No stocks found, no history -> setting fallback guide"
            )
        else:
            from .entity_extractor import _group_messages_into_turns
            turns = _group_messages_into_turns(messages)
            found = False

            for turn in reversed(turns[-3:]):
                user_content, ai_content = turn

                # Search user message first
                if user_content:
                    try:
                        history_stock = await _resolve_stocks(user_content, market)
                        if history_stock["stock_codes"]:
                            entities["stock_names"] = history_stock["stock_names"]
                            entities["stock_codes"] = history_stock["stock_codes"]
                            entities["stock_info"] = history_stock["stock_info"]
                            logger.info(
                                f"[UnifiedClassifier] Fallback from user turn: "
                                f"{history_stock['stock_names']}"
                            )
                            found = True
                            break
                    except Exception:
                        pass

                # Search AI response (exact match only)
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
                                f"[UnifiedClassifier] Fallback from AI turn (exact only): "
                                f"{ai_stock['stock_names']}"
                            )
                            found = True
                            break
                    except Exception:
                        pass

            if not found:
                entities["stock_fallback_guide"] = True
                logger.info(
                    "[UnifiedClassifier] No stocks found in 3 recent turns "
                    "-> setting fallback guide"
                )

    # === Query expansion for better retrieval (rule-based, not LLM) ===
    try:
        query_expander = _get_query_expander()
        expansion = await query_expander.expand(
            message, use_synonyms=True, use_rewrite=False
        )
        entities["keywords"] = expansion.get("keywords", [])
        entities["expanded_queries"] = expansion.get("expanded", [message])
    except Exception as e:
        logger.debug(f"[UnifiedClassifier] Query expansion failed: {e}")
        entities["keywords"] = []
        entities["expanded_queries"] = [message]

    logger.info(
        f"[AlphaAI:UnifiedClassifier] Intent: {intent}, Market: {market}, "
        f"StockScope: {stock_scope}, "
        f"Stocks: {len(entities.get('stock_names', []))}, "
        f"Indicators: {len(entities.get('indicators', []))}"
        f"{f', Expanded: {expanded_message}' if expanded_message else ''}"
    )

    return {
        **state,
        "intent": intent,
        "market": market,
        "stock_scope": stock_scope,
        "entities": entities,
        **({"expanded_message": expanded_message} if expanded_message else {}),
        "processing_steps": state.get("processing_steps", []) + ["unified_classifier"],
    }
