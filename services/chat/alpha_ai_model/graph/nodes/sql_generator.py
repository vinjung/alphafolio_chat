# services/chat/alpha_ai_model/graph/nodes/sql_generator.py
"""
SQL Generation Node

Generates PostgreSQL queries using LLM from:
- User intent and entities
- Relevant schema information
- Few-shot examples
"""
import math
from typing import Dict, Any
from config import logger, settings
from core.llm.factory import get_llm, LLMProvider

from ...prompts.sql_prompt import (
    get_sql_prompt,
    get_schema_by_market,
    get_default_term_mapping
)
from ...prompts.sql_prompt_finetuned import get_finetuned_sql_prompt
from ...prompts.few_shot_examples import (
    get_similar_examples,
    format_few_shot_for_prompt
)


def format_conversation_context(messages: list) -> str:
    """
    Format conversation history for SQL generation context

    Args:
        messages: List of LangChain messages (HumanMessage, AIMessage)

    Returns:
        Formatted conversation context string
    """
    if not messages:
        return ""

    context_lines = []
    # Take only last 4 messages (2 turns) to keep context focused
    recent_messages = messages[-4:] if len(messages) > 4 else messages

    for msg in recent_messages:
        role = "User" if msg.__class__.__name__ == "HumanMessage" else "Assistant"
        # Truncate long messages to avoid bloating the prompt
        content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
        context_lines.append(f"{role}: {content}")

    return "\n".join(context_lines)


async def generate_sql_with_llm(
    message: str,
    intent: str,
    market: str,
    entities: Dict[str, Any],
    provider: str = None,
    model: str = None,
    state: Dict[str, Any] = None
) -> str:
    """
    Generate SQL using LLM

    Args:
        message: User's question
        intent: Classified intent
        market: KR or US
        entities: Extracted entities
        provider: LLM provider
        model: Model name
        state: Graph state containing RAG results

    Returns:
        Generated SQL string
    """
    try:
        # Determine if fine-tuned model should be used
        retry_count = state.get("sql_retry_count", 0) if state else 0
        table_count = len(state.get("relevant_tables", [])) if state else 0
        use_finetuned = (
            settings.fine_tuned_sql_enabled
            and settings.fine_tuned_sql_model
            and LLMProvider.OPENAI in settings.available_llms
            and retry_count == 0  # Only use fine-tuned on first attempt
            and table_count <= settings.fine_tuned_max_tables
        )

        if (settings.fine_tuned_sql_enabled
                and retry_count == 0
                and table_count > settings.fine_tuned_max_tables):
            logger.info(
                f"[SQLGenerator] Complexity routing: {table_count} tables > "
                f"threshold {settings.fine_tuned_max_tables}, using Claude directly"
            )

        if not use_finetuned and retry_count > 0 and settings.fine_tuned_sql_enabled:
            previous_error = state.get("sql_error", "") if state else ""
            logger.info(
                f"[SQLGenerator] Fine-tuned model failed, falling back to Claude "
                f"(retry {retry_count}, error: {previous_error[:200]})"
            )

        # Get LLM instance
        if use_finetuned:
            llm = get_llm(
                LLMProvider.OPENAI,
                model_name=settings.fine_tuned_sql_model,
                streaming=False,
                max_tokens=4096
            )
            model_used = settings.fine_tuned_sql_model
            logger.info(f"[SQLGenerator] Using fine-tuned model: {model_used}")
        else:
            llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
            llm = get_llm(llm_provider, model_name=model)
            model_used = model or str(llm_provider.value)

        # Get schema for market - prefer RAG result from state
        if state and state.get("schema_context"):
            schema_info = state.get("schema_context")
        else:
            schema_info = get_schema_by_market(market)

        # Get term mapping - prefer RAG result from state
        if state and state.get("term_context"):
            term_mapping = state.get("term_context")
        else:
            term_mapping = get_default_term_mapping()

        # Get conversation context from state
        conversation_context = ""
        if state and state.get("messages"):
            conversation_context = format_conversation_context(state.get("messages"))
            if conversation_context:
                logger.debug(f"[SQLGenerator] Using conversation context: {len(state.get('messages'))} messages")

        # Create prompt - branching based on model type
        if use_finetuned:
            prompt = get_finetuned_sql_prompt(
                user_question=message,
                schema_info=schema_info,
                term_mapping=term_mapping,
                conversation_context=conversation_context
            )
        else:
            # Get similar examples for standard prompt
            if state and state.get("few_shot_examples"):
                examples = state.get("few_shot_examples")
                few_shot_text = format_few_shot_for_prompt(examples)
            else:
                examples = get_similar_examples(intent, market, limit=3)
                few_shot_text = format_few_shot_for_prompt(examples)

            prompt = get_sql_prompt(
                user_question=message,
                schema_info=schema_info,
                term_mapping=term_mapping,
                few_shot_examples=few_shot_text,
                conversation_context=conversation_context
            )

        # Get response
        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Extract SQL from response
        sql = extract_sql_from_response(response_text)

        # Store model info in state for tracking
        if state is not None:
            state["sql_model_used"] = model_used

        return sql

    except Exception as e:
        logger.error(f"[SQLGenerator] LLM generation error: {e}")
        raise


def extract_sql_from_response(response: str) -> str:
    """
    Extract SQL from LLM response

    Args:
        response: Raw LLM response

    Returns:
        Cleaned SQL string
    """
    if not response:
        return ""

    sql = response.strip()

    # Remove markdown code blocks
    if "```sql" in sql:
        parts = sql.split("```sql")
        if len(parts) >= 2:
            sql = parts[1]
            if "```" in sql:
                sql = sql.split("```")[0]
        else:
            sql = ""
    elif "```" in sql:
        parts = sql.split("```")
        if len(parts) >= 2:
            sql = parts[1]

    # Clean up
    sql = sql.strip()

    # Remove any trailing semicolons and add one
    sql = sql.rstrip(';').strip()

    return sql


def generate_fallback_sql(
    intent: str,
    market: str,
    entities: Dict[str, Any]
) -> str:
    """
    Generate fallback SQL when LLM fails

    Args:
        intent: User intent
        market: KR, US, or BOTH
        entities: Extracted entities

    Returns:
        Fallback SQL string
    """
    limit = (entities.get("limit") or 10) if entities else 10
    stock_codes = entities.get("stock_codes", []) if entities else []

    # Handle BOTH market with UNION queries
    if market == "BOTH":
        kr_limit = math.ceil(limit / 2)
        us_limit = max(limit - kr_limit, 1)

        if intent == "ranking":
            return f"""(SELECT symbol, stock_name, close, volume, change_rate, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY volume DESC
LIMIT {kr_limit})
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, d.volume, d.change_rate, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY d.volume DESC
LIMIT {us_limit})"""

        elif intent == "technical":
            return f"""(SELECT k.symbol, k.stock_name, k.close, i.rsi, 'KR' as market
FROM kr_intraday_total k
JOIN kr_indicators i ON k.symbol = i.symbol AND k.date = i.date
WHERE i.date = (SELECT MAX(date) FROM kr_indicators)
ORDER BY i.rsi ASC
LIMIT {kr_limit})
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, i.rsi, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators)
ORDER BY i.rsi ASC
LIMIT {us_limit})"""

        elif intent == "quant":
            return f"""(SELECT k.symbol, k.stock_name, g.final_grade, g.final_score, 'KR' as market
FROM kr_intraday_total k
JOIN kr_stock_grade g ON k.symbol = g.symbol
WHERE k.date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY g.final_score DESC
LIMIT {kr_limit})
UNION ALL
(SELECT d.symbol, s.stock_name, g.final_grade, g.final_score, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_stock_grade g ON d.symbol = g.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY g.final_score DESC
LIMIT {us_limit})"""

        else:
            return f"""(SELECT symbol, stock_name, close, volume, change_rate, 'KR' as market
FROM kr_intraday_total
WHERE date = (SELECT MAX(date) FROM kr_intraday_total)
ORDER BY volume DESC
LIMIT {kr_limit})
UNION ALL
(SELECT d.symbol, s.stock_name, d.close, d.volume, d.change_rate, 'US' as market
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY d.volume DESC
LIMIT {us_limit})"""

    # Single market queries
    if market == "KR":
        main_table = "kr_intraday"

        if intent == "ranking":
            return f"""SELECT symbol, stock_name, close, volume, trading_value, market_cap, change_rate
FROM {main_table}
ORDER BY trading_value DESC
LIMIT {limit}"""

        elif intent == "filter":
            return f"""SELECT symbol, stock_name, close, volume, trading_value, market_cap
FROM {main_table}
WHERE market_cap >= 1000000000000
ORDER BY market_cap DESC
LIMIT 20"""

        elif intent == "technical":
            return f"""SELECT k.symbol, k.stock_name, k.close, i.rsi, i.macd
FROM {main_table} k
JOIN kr_indicators i ON k.symbol = i.symbol
WHERE i.date = CURRENT_DATE
ORDER BY i.rsi ASC
LIMIT 20"""

        elif intent == "market":
            return """SELECT exchange, close, change_rate, volume, trading_value
FROM market_index
WHERE exchange = 'KOSPI'
ORDER BY date DESC
LIMIT 1"""

        elif intent == "query" and stock_codes:
            code = stock_codes[0]
            return f"""SELECT symbol, stock_name, close, open, high, low, volume, change_rate
FROM {main_table}
WHERE symbol = '{code}'"""

        else:
            return f"""SELECT symbol, stock_name, close, volume, trading_value
FROM {main_table}
ORDER BY trading_value DESC
LIMIT 10"""

    else:
        # US market - JOIN us_stock_basic for stock_name and market_cap
        if intent == "ranking":
            return f"""SELECT d.symbol, s.stock_name, d.close, d.volume, s.market_cap, d.change_rate
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY d.volume DESC
LIMIT {limit}"""

        elif intent == "filter":
            return """SELECT d.symbol, s.stock_name, d.close, d.volume, s.market_cap
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily) AND s.market_cap >= 1000000000000
ORDER BY s.market_cap DESC
LIMIT 20"""

        elif intent == "technical":
            return """SELECT d.symbol, s.stock_name, d.close, i.rsi, i.macd
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
JOIN us_indicators i ON d.symbol = i.symbol AND d.date = i.date
WHERE i.date = (SELECT MAX(date) FROM us_indicators)
ORDER BY i.rsi ASC
LIMIT 20"""

        elif intent == "market":
            return """SELECT exchange, close, change_rate, volume, trading_value
FROM market_index
WHERE exchange = 'NASDAQ'
ORDER BY date DESC
LIMIT 1"""

        elif intent == "query" and stock_codes:
            code = stock_codes[0]
            return f"""SELECT d.symbol, s.stock_name, d.close, d.open, d.high, d.low, d.volume, d.change_rate
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.symbol = '{code}' AND d.date = (SELECT MAX(date) FROM us_daily WHERE symbol = '{code}')"""

        else:
            return """SELECT d.symbol, s.stock_name, d.close, d.volume
FROM us_daily d
JOIN us_stock_basic s ON d.symbol = s.symbol
WHERE d.date = (SELECT MAX(date) FROM us_daily)
ORDER BY d.volume DESC
LIMIT 10"""


async def sql_generator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate SQL query from natural language using LLM

    Args:
        state: Current graph state with schema and entity information

    Returns:
        Updated state with 'generated_sql' field
    """
    logger.info("[AlphaAI:SQLGenerator] Processing...")

    message = state.get("message", "")
    intent = state.get("intent", "query")
    market = state.get("market", "KR")
    entities = state.get("entities", {})
    provider = state.get("provider")
    model = state.get("model_name")

    try:
        # Generate SQL with LLM - pass state for RAG results
        generated_sql = await generate_sql_with_llm(
            message=message,
            intent=intent,
            market=market,
            entities=entities,
            provider=provider,
            model=model,
            state=state
        )
        logger.info(f"[AlphaAI:SQLGenerator] Generated SQL:\n{generated_sql}")

    except Exception as e:
        logger.warning(f"[SQLGenerator] Primary LLM failed: {e}")
        try:
            logger.info("[SQLGenerator] Retrying with GPT-4.1 fallback...")
            generated_sql = await generate_sql_with_llm(
                message=message,
                intent=intent,
                market=market,
                entities=entities,
                provider="openai",
                model="gpt-4.1",
                state=state
            )
            logger.info(f"[AlphaAI:SQLGenerator] GPT-4.1 Fallback SQL:\n{generated_sql}")
        except Exception as e2:
            logger.warning(f"[SQLGenerator] GPT-4.1 fallback also failed: {e2}, using template")
            generated_sql = generate_fallback_sql(intent, market, entities)
            logger.info(f"[AlphaAI:SQLGenerator] Template Fallback SQL:\n{generated_sql}")

    # Preserve retry count from state (don't reset to 0)
    current_retry_count = state.get("sql_retry_count", 0)

    return {
        **state,
        "generated_sql": generated_sql,
        "sql_model_used": state.get("sql_model_used"),
        "sql_retry_count": current_retry_count,
        "processing_steps": state.get("processing_steps", []) + ["sql_generator"]
    }
