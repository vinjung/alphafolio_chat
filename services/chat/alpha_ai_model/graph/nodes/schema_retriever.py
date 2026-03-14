# services/chat/alpha_ai_model/graph/nodes/schema_retriever.py
"""
Schema Retrieval Node

Retrieves relevant schema information using RAG:
- Table schemas
- Column descriptions
- Few-shot SQL examples
- Term mappings
"""
from typing import Dict, Any, List
from config import logger, settings

from ...rag import SchemaRAG, FewShotRAG, TermMapper, QueryExpander, SelfQueryRetriever
from ...prompts.sql_prompt import get_schema_by_market


# Global RAG instances (initialized lazily)
_schema_rag: SchemaRAG = None
_few_shot_rag: FewShotRAG = None
_term_mapper: TermMapper = None
_query_expander: QueryExpander = None
_self_query: SelfQueryRetriever = None


async def get_schema_rag() -> SchemaRAG:
    """Get or initialize SchemaRAG instance"""
    global _schema_rag
    if _schema_rag is None:
        _schema_rag = SchemaRAG()
    return _schema_rag


async def get_few_shot_rag() -> FewShotRAG:
    """Get or initialize FewShotRAG instance"""
    global _few_shot_rag
    if _few_shot_rag is None:
        _few_shot_rag = FewShotRAG()
    return _few_shot_rag


def get_term_mapper() -> TermMapper:
    """Get or initialize TermMapper instance"""
    global _term_mapper
    if _term_mapper is None:
        _term_mapper = TermMapper()
    return _term_mapper


def get_query_expander() -> QueryExpander:
    """Get or initialize QueryExpander instance (rule-based only)"""
    global _query_expander
    if _query_expander is None:
        _query_expander = QueryExpander(use_llm=False)
    return _query_expander


def get_self_query() -> SelfQueryRetriever:
    """Get or initialize SelfQueryRetriever instance (rule-based only)"""
    global _self_query
    if _self_query is None:
        _self_query = SelfQueryRetriever(use_llm=False)
    return _self_query


async def schema_retriever(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve relevant schema information for SQL generation

    Uses RAG to find:
    1. Relevant tables based on query semantics
    2. Similar few-shot SQL examples
    3. Term mappings for the query

    Args:
        state: Current graph state with 'intent', 'market', 'entities' fields

    Returns:
        Updated state with 'relevant_tables', 'relevant_columns', 'few_shot_examples'
    """
    logger.info("[AlphaAI:SchemaRetriever] Processing...")

    # Use expanded_message (from query rewriting) if available, fallback to original
    message = state.get("expanded_message") or state.get("message", "")
    market = state.get("market", "KR")
    intent = state.get("intent", "query")
    entities = state.get("entities", {})

    # Get RAG components
    schema_rag = await get_schema_rag()
    few_shot_rag = await get_few_shot_rag()
    term_mapper = get_term_mapper()
    query_expander = get_query_expander()
    self_query = get_self_query()

    try:
        # 0. Query expansion (rule-based)
        keywords = query_expander.extract_keywords(message)
        normalized_query = query_expander.normalize_query(message)
        logger.info(f"[AlphaAI:SchemaRetriever] QueryExpander - keywords: {keywords}, normalized: {normalized_query[:80]}")

        # 0b. Self-query structured extraction (rule-based)
        sq_filters = self_query._extract_filters_rule_based(message)
        sq_sort = self_query._extract_sort(message)
        sq_limit = self_query._extract_limit(message)
        sq_tables = self_query._infer_tables(sq_filters, sq_sort, market)
        logger.info(f"[AlphaAI:SchemaRetriever] SelfQuery - filters: {len(sq_filters)}, sort: {sq_sort}, limit: {sq_limit}, tables: {sq_tables}")

        # 1. Retrieve relevant tables using SchemaRAG
        stock_codes = entities.get("stock_codes", [])
        tables_info = await schema_rag.retrieve_tables(
            query=normalized_query or message,
            market=market,
            top_k=5,
            stock_codes=stock_codes
        )

        relevant_tables = [t["table"] for t in tables_info]

        # Merge tables from SelfQueryRetriever
        for table in sq_tables:
            if table not in relevant_tables:
                relevant_tables.append(table)

        logger.info(f"[AlphaAI:SchemaRetriever] Found tables: {relevant_tables}")

        # 2. Retrieve relevant columns
        relevant_columns = await schema_rag.retrieve_columns(
            query=normalized_query or message,
            tables=relevant_tables,
            top_k=15
        )

        # 3. Retrieve few-shot examples using FewShotRAG
        if keywords:
            few_shot_examples = await few_shot_rag.hybrid_retrieve(
                query=normalized_query or message,
                intent=intent,
                market=market,
                top_k=5
            )
        else:
            few_shot_examples = await few_shot_rag.retrieve_examples(
                query=message,
                intent=intent,
                market=market,
                top_k=5
            )

        # Format examples for state
        formatted_examples = []
        for example in few_shot_examples:
            formatted_examples.append({
                "question": example.get("question", ""),
                "sql": example.get("sql", ""),
                "category": example.get("category", "query"),
                "chart_indicators": example.get("chart_indicators", False)
            })

        logger.info(f"[AlphaAI:SchemaRetriever] Found {len(formatted_examples)} few-shot examples")

        # 4. Get term mappings
        term_context = term_mapper.format_for_prompt(message, market)
        required_tables = term_mapper.get_required_tables(message, market)

        # Merge required tables
        for table in required_tables:
            if table not in relevant_tables:
                relevant_tables.append(table)

        # 5. Get SQL conditions from terms
        sql_conditions = term_mapper.get_sql_conditions(message, market)

        # Update entities with extracted conditions
        updated_entities = entities.copy() if entities else {}
        if sql_conditions:
            updated_entities["sql_conditions"] = sql_conditions

        # Store SelfQuery results in entities
        if sq_filters:
            updated_entities["self_query_filters"] = [
                {"column": f.column, "operator": f.operator.value if hasattr(f.operator, 'value') else str(f.operator), "value": f.value}
                for f in sq_filters
            ]
        if sq_sort:
            updated_entities["self_query_sort"] = {"column": sq_sort.column, "direction": sq_sort.direction}
        if sq_limit:
            updated_entities["self_query_limit"] = sq_limit

        # Get schema context for prompt
        # For complex queries, use full market schema to prevent column hallucination
        # (RAG retrieves only 5-9 tables, but complex queries need 10+ with exact column names)
        if len(relevant_tables) > settings.fine_tuned_max_tables:
            schema_context = get_schema_by_market(market)
            logger.info(
                f"[SchemaRetriever] Full schema mode: {len(relevant_tables)} tables detected, "
                f"injecting all {market} schemas to prevent column hallucination"
            )
        else:
            schema_context = await schema_rag.get_schema_context(
                query=normalized_query or message,
                market=market,
                max_tables=5
            )

        logger.info(f"[AlphaAI:SchemaRetriever] Complete - Tables: {len(relevant_tables)}, Examples: {len(formatted_examples)}")

        return {
            **state,
            "relevant_tables": relevant_tables,
            "relevant_columns": relevant_columns,
            "few_shot_examples": formatted_examples,
            "schema_context": schema_context,
            "term_context": term_context,
            "entities": updated_entities,
            "processing_steps": state.get("processing_steps", []) + ["schema_retriever"]
        }

    except Exception as e:
        logger.error(f"[AlphaAI:SchemaRetriever] RAG error: {e}")

        # Fallback to basic retrieval without RAG
        return await _fallback_retrieval(state, market, intent, entities)


async def _fallback_retrieval(
    state: Dict[str, Any],
    market: str,
    intent: str,
    entities: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fallback retrieval without RAG (in case of errors)

    Args:
        state: Current graph state
        market: Market (KR/US)
        intent: Query intent
        entities: Extracted entities

    Returns:
        Updated state with basic schema info
    """
    logger.warning("[AlphaAI:SchemaRetriever] Using fallback retrieval")

    # Determine KR default table based on market hours
    kr_default_table = "kr_intraday_total"
    try:
        schema_rag = await get_schema_rag()
        if await schema_rag._is_kr_market_open():
            kr_default_table = "kr_intraday"
    except Exception:
        pass

    # Default tables based on market
    if market == "KR":
        relevant_tables = [kr_default_table, "kr_indicators", "kr_stock_basic"]
    elif market == "US":
        relevant_tables = ["us_daily", "us_indicators", "us_stock_basic"]
    elif market == "BOTH":
        relevant_tables = [kr_default_table, "kr_indicators", "us_daily", "us_indicators"]
    else:
        relevant_tables = [kr_default_table, "kr_indicators", "kr_stock_basic"]

    # Add tables based on intent
    if intent == "technical":
        if market in ("KR", "BOTH"):
            relevant_tables.append("kr_indicators")
        if market in ("US", "BOTH"):
            relevant_tables.append("us_indicators")
    elif intent == "investor" and market in ("KR", "BOTH"):
        relevant_tables.append("kr_individual_investor_daily_trading")
    elif intent == "quant":
        if market in ("KR", "BOTH"):
            relevant_tables.append("kr_stock_grade")
        if market in ("US", "BOTH"):
            relevant_tables.append("us_stock_grade")
    elif intent == "analysis":
        if market in ("KR", "BOTH"):
            relevant_tables.append("kr_stock_grade")
        if market in ("US", "BOTH"):
            relevant_tables.append("us_stock_grade")
    elif intent == "market":
        relevant_tables.append("market_index")

    # Add daily_recommendation for strategy-type questions without specific stock
    if not entities.get("stock_codes") and intent in ("query", "analysis", "quant"):
        relevant_tables.append("daily_recommendation")

    # Remove duplicates
    relevant_tables = list(set(relevant_tables))

    # Basic column info
    relevant_columns = [
        {"table": relevant_tables[0], "column": "symbol", "type": "VARCHAR", "description": "Stock code"},
        {"table": relevant_tables[0], "column": "close", "type": "NUMERIC", "description": "Closing price"},
        {"table": relevant_tables[0], "column": "volume", "type": "BIGINT", "description": "Trading volume"},
    ]

    # Basic few-shot examples
    few_shot_examples = [
        {
            "question": "거래대금 상위 10개 종목",
            "sql": "SELECT symbol, stock_name, close, trading_value FROM kr_intraday ORDER BY trading_value DESC LIMIT 10",
            "category": "ranking"
        },
        {
            "question": "RSI 30 이하 종목",
            "sql": "SELECT k.symbol, k.stock_name, i.rsi FROM kr_intraday k JOIN kr_indicators i ON k.symbol = i.symbol WHERE i.rsi < 30 AND i.date = CURRENT_DATE",
            "category": "filter"
        }
    ]

    return {
        **state,
        "relevant_tables": relevant_tables,
        "relevant_columns": relevant_columns,
        "few_shot_examples": few_shot_examples,
        "processing_steps": state.get("processing_steps", []) + ["schema_retriever"]
    }
