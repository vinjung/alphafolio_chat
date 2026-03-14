# services/chat/alpha_ai_model/graph/nodes/parallel_sql_pipeline.py
"""
Parallel SQL Pipeline Node

Executes SQL pipeline for each sub-query in parallel:
  For each sub-query: schema assembly -> few-shot -> SQL gen -> validate -> execute

Handles dependency chains: independent sub-queries run in parallel first,
then dependent sub-queries run grouped by dependency level.

Feature flag: USE_QUERY_DECOMPOSITION (default: False)
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from config import logger
from database import db
from core.llm.factory import get_llm, LLMProvider

from ...prompts.sql_prompt import (
    get_sql_prompt,
    get_schema_for_tables,
    get_schema_by_market,
    get_default_term_mapping,
)
from ...prompts.few_shot_examples import format_few_shot_for_prompt
from ...tools.sql_tools import SQLTools
from .sql_validator import (
    validate_table_names,
    validate_with_explain,
    get_common_fixes,
    check_sql_structure,
    extract_table_names,
)
from .sql_generator import extract_sql_from_response, format_conversation_context


# Tables that clearly indicate macro/index data (never merge with stock screening)
_MACRO_TABLES = {
    "us_vix", "us_cpi", "us_fed_funds_rate", "us_treasury_yield",
    "us_gdp", "us_pmi", "us_unemployment_rate", "us_market_regime",
    "us_dollar_index", "us_credit_spread", "us_fed_rrp", "us_move_index",
    "bok_economic_indicators", "market_index", "exchange_rate",
    "kr_benchmark_index", "mv_sector_daily_performance",
    "mv_us_sector_daily_performance",
}

# Screening action/connector keywords
_SCREENING_CONNECTORS = [
    "이고", "이면서", "하고", "동시에",
    "찾아줘", "찾아", "골라줘", "골라",
    "필터링", "스크리닝", "screening",
]


def _maybe_merge_screening_subqueries(
    sub_queries: List[Dict[str, Any]],
    message: str,
) -> List[Dict[str, Any]]:
    """
    Code-level safety net: if multiple independent sub-queries all do
    stock-filtering on the same market, merge them into a single CTE query.

    Only merges when:
    - Message contains screening connectors
    - 2+ independent (depends_on=None) sub-queries exist
    - All independent stock-filter sub-queries target same market
    - Sub-queries use stock-level tables (not macro/index)
    """
    msg_lower = message.lower()
    if not any(kw in msg_lower for kw in _SCREENING_CONNECTORS):
        return sub_queries

    independent = [(i, sq) for i, sq in enumerate(sub_queries) if sq.get("depends_on") is None]
    dependent = [(i, sq) for i, sq in enumerate(sub_queries) if sq.get("depends_on") is not None]

    if len(independent) < 2:
        return sub_queries

    # Separate stock-filter vs macro queries
    stock_filter_sqs = []
    macro_sqs = []
    for i, sq in independent:
        tables = set(sq.get("tables", []))
        if tables and tables.issubset(_MACRO_TABLES):
            macro_sqs.append((i, sq))
        else:
            stock_filter_sqs.append((i, sq))

    if len(stock_filter_sqs) < 2:
        return sub_queries

    # All stock-filter queries must target same market
    markets = set(sq.get("market") for _, sq in stock_filter_sqs)
    if len(markets) > 1:
        return sub_queries

    target_market = markets.pop()

    # Merge: combine questions and tables
    merged_tables = []
    merged_questions = []
    old_to_new_index = {}

    for i, sq in stock_filter_sqs:
        merged_questions.append(sq["question"])
        for t in sq.get("tables", []):
            if t not in merged_tables:
                merged_tables.append(t)
        old_to_new_index[i] = 0

    # Ensure stock_name source table
    if target_market == "KR":
        if "kr_intraday_total" not in merged_tables and "kr_intraday" not in merged_tables:
            merged_tables.insert(0, "kr_intraday_total")
    elif target_market == "US":
        if "us_daily" not in merged_tables and "us_stock_basic" not in merged_tables:
            merged_tables.insert(0, "us_daily")

    merged_sq = {
        "question": (
            "[SCREENING QUERY - Use CTE to combine ALL conditions in ONE SQL] "
            + " AND ".join(merged_questions)
        ),
        "market": target_market,
        "tables": merged_tables,
        "depends_on": None,
    }

    result = [merged_sq]

    # Re-map macro queries (keep independent)
    for i, sq in macro_sqs:
        old_to_new_index[i] = len(result)
        result.append(sq)

    # Re-map dependent queries (update depends_on index)
    for i, sq in dependent:
        old_dep = sq.get("depends_on")
        new_dep = old_to_new_index.get(old_dep, 0)
        old_to_new_index[i] = len(result)
        result.append({**sq, "depends_on": new_dep})

    logger.info(
        f"[ParallelSQL] Screening merger: {len(sub_queries)} -> {len(result)} sub-queries "
        f"(merged {len(stock_filter_sqs)} independent into 1)"
    )

    return result


def _fix_stock_symbols_in_sql(sql: str, stock_info: list) -> str:
    """Fix stock symbol references in SQL using StockResolver results."""
    if not stock_info:
        return sql

    import re
    fixed_sql = sql

    for si in stock_info:
        name = si.get("name", "")
        symbol = si.get("symbol", "")
        if not name or not symbol:
            continue

        # Fix 1: stock_name = 'name' -> symbol = 'code'
        pattern = r"(\w+\.)?stock_name\s*=\s*'" + re.escape(name) + r"'"
        fixed_sql = re.sub(pattern, r"\g<1>symbol = '" + symbol + "'", fixed_sql)

        # Fix 2: stock_name LIKE '%name%' -> symbol = 'code'
        pattern_like = r"(\w+\.)?stock_name\s+(?:I?LIKE)\s+'%?" + re.escape(name) + r"%?'"
        fixed_sql = re.sub(pattern_like, r"\g<1>symbol = '" + symbol + "'", fixed_sql)

        # Fix 3: matched_term variation (e.g., fuzzy match input)
        matched_term = si.get("matched_term", "")
        if matched_term and matched_term != name:
            pattern_mt = r"(\w+\.)?stock_name\s*=\s*'" + re.escape(matched_term) + r"'"
            fixed_sql = re.sub(pattern_mt, r"\g<1>symbol = '" + symbol + "'", fixed_sql)

    if fixed_sql != sql:
        logger.info(f"[ParallelSQL] Stock symbol fix applied")

    return fixed_sql


def _get_rag_instances():
    """Get RAG singleton instances from schema_retriever module."""
    from .schema_retriever import get_few_shot_rag, get_term_mapper
    return get_few_shot_rag, get_term_mapper


async def _build_schema_context(tables: List[str], market: str) -> str:
    """
    Build schema context for SQL generation.

    Uses get_schema_for_tables for targeted schema when table list is small,
    falls back to full market schema for larger table lists.

    Args:
        tables: List of table names assigned by decomposer
        market: Market identifier (KR/US)

    Returns:
        Schema context string for LLM prompt
    """
    if not tables:
        return get_schema_by_market(market)

    schema = get_schema_for_tables(tables)
    if schema and schema != "No schema information available.":
        return schema

    # Fallback to full market schema if specific tables not found
    return get_schema_by_market(market)


async def _execute_sub_query(
    sub_query: Dict[str, Any],
    message: str,
    entities: Dict[str, Any],
    provider: str,
    model: str,
    conversation_context: str = "",
    dependency_result: Optional[List[Dict]] = None,
    sub_query_index: int = 0,
) -> Dict[str, Any]:
    """
    Execute a single sub-query through the full SQL pipeline:
    1. Schema assembly from assigned tables
    2. Few-shot retrieval
    3. Term mapping
    4. SQL generation (LLM)
    5. Validation (security + table + EXPLAIN)
    6. Execution
    7. If failed, pattern-based retry once

    Args:
        sub_query: Sub-query dict with question, market, tables, depends_on
        message: Original user message (for context)
        entities: Extracted entities from decomposer
        provider: LLM provider string
        model: Model name string
        conversation_context: Formatted conversation history
        dependency_result: Results from dependency sub-query (if depends_on is set)

    Returns:
        Result dict with question, market, tables, sql, result, result_count, error, model_used
    """
    sq_question = sub_query["question"]
    sq_market = sub_query["market"]
    sq_tables = sub_query["tables"]

    result = {
        "question": sq_question,
        "market": sq_market,
        "tables": sq_tables,
        "sql": None,
        "result": [],
        "result_count": 0,
        "error": None,
        "model_used": None,
        "sub_query_index": sub_query_index,
    }

    try:
        # 1. Build schema context from assigned tables
        schema_info = await _build_schema_context(sq_tables, sq_market)

        # 2. Few-shot retrieval
        get_few_shot_rag, get_term_mapper = _get_rag_instances()
        few_shot_rag = await get_few_shot_rag()
        few_shot_examples = await few_shot_rag.hybrid_retrieve(
            query=sq_question,
            market=sq_market,
            top_k=3,
        )
        few_shot_text = format_few_shot_for_prompt(few_shot_examples)

        # 3. Term mapping
        term_mapper = get_term_mapper()
        term_mapping = term_mapper.format_for_prompt(sq_question, sq_market)

        # 4. Build dependency context if available
        dep_context = ""
        if dependency_result:
            # Provide summary of dependency results to help SQL generation
            dep_symbols = set()
            for row in dependency_result[:20]:  # Limit context size
                if "symbol" in row:
                    dep_symbols.add(str(row["symbol"]))
            if dep_symbols:
                dep_context = (
                    f"\n\n## Context from prior query results (MANDATORY FILTER)\n"
                    f"These symbols passed all prior filtering conditions: {', '.join(list(dep_symbols)[:30])}\n"
                    f"REQUIRED: Your SQL MUST include WHERE symbol IN ({', '.join(repr(s) for s in list(dep_symbols)[:30])})\n"
                    f"For date filtering, use MAX(date) from the TARGET table you are querying, NOT dates from prior results."
                )

        # 4-1. Build stock code context from StockResolver results
        stock_context = ""
        stock_info_list = entities.get("stock_info", [])
        if stock_info_list:
            mappings = []
            for si in stock_info_list:
                mappings.append(f"  {si['name']} -> symbol = '{si['symbol']}'")
            stock_context = (
                "\n\n## Resolved Stock Codes (MUST use these exact symbol values in WHERE clauses)\n"
                + "\n".join(mappings)
            )

        # 5. Generate SQL with LLM
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)
        model_used = model or str(llm_provider.value)

        prompt = get_sql_prompt(
            user_question=sq_question + dep_context + stock_context,
            schema_info=schema_info,
            term_mapping=term_mapping,
            few_shot_examples=few_shot_text,
            conversation_context=conversation_context,
        )

        # LLM call with retry (API errors: overloaded, internal_server_error)
        max_api_retries = 2
        for attempt in range(max_api_retries + 1):
            try:
                response = await llm.ainvoke(prompt)
                break
            except Exception as e:
                error_str = str(e)
                is_retryable = any(keyword in error_str.lower() for keyword in [
                    "overloaded", "internal server error", "api_error", "rate_limit",
                    "529", "500", "503"
                ])
                if is_retryable and attempt < max_api_retries:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"[ParallelSQL] API error (attempt {attempt+1}/{max_api_retries+1}), retrying in {wait_time}s: {error_str[:100]}")
                    await asyncio.sleep(wait_time)
                    continue
                raise
        response_text = response.content if hasattr(response, 'content') else str(response)
        sql = extract_sql_from_response(response_text)

        if not sql:
            result["error"] = "Empty SQL generated"
            logger.warning(f"[ParallelSQL] Empty SQL for: {sq_question[:60]}")
            return result

        result["sql"] = sql
        result["model_used"] = model_used
        logger.info(f"[ParallelSQL] Generated SQL for '{sq_question[:50]}':\n{sql}")

        # 5-1. Fix stock symbols using StockResolver results
        sql = _fix_stock_symbols_in_sql(sql, stock_info_list)
        result["sql"] = sql

        # 6. Validate SQL
        valid, error_msg = await _validate_sql(sql, sq_market)
        if not valid:
            # Try pattern-based fix (includes HINT-based alias fix)
            logger.info(f"[ParallelSQL] Validation failed, trying fix: {error_msg[:100]}")
            fixed_sql = get_common_fixes(sql, error_msg)
            if fixed_sql != sql:
                valid, error_msg = await _validate_sql(fixed_sql, sq_market)
                if valid:
                    sql = fixed_sql
                    result["sql"] = sql
                    logger.info("[ParallelSQL] Pattern fix successful")

            # Try LLM-based SQL repair as last resort
            if not valid:
                logger.info(f"[ParallelSQL] Pattern fix failed, trying LLM repair for: {sq_question[:60]}")
                repaired_sql = await _llm_repair_sql(
                    sql, error_msg, sq_question, schema_info, provider, model
                )
                if repaired_sql and repaired_sql != sql:
                    valid, error_msg = await _validate_sql(repaired_sql, sq_market)
                    if valid:
                        sql = repaired_sql
                        result["sql"] = sql
                        logger.info("[ParallelSQL] LLM repair successful")

            if not valid:
                result["error"] = f"SQL validation failed: {error_msg[:200]}"
                logger.warning(f"[ParallelSQL] Validation failed for: {sq_question[:60]}")
                return result

        # 7. Execute SQL
        exec_result, exec_error = await _execute_sql(sql)
        if exec_error:
            result["error"] = exec_error
            logger.warning(f"[ParallelSQL] Execution failed for: {sq_question[:60]}: {exec_error[:100]}")
            return result

        result["result"] = exec_result
        result["result_count"] = len(exec_result)

        logger.info(
            f"[ParallelSQL] Sub-query success: '{sq_question[:50]}' -> "
            f"{result['result_count']} rows"
        )

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[ParallelSQL] Exception for '{sq_question[:50]}': {e}")

    return result


async def _llm_repair_sql(
    sql: str,
    error_msg: str,
    question: str,
    schema_info: str,
    provider: str = None,
    model: str = None,
) -> Optional[str]:
    """
    Use LLM to repair a failed SQL query based on the validation error.

    Args:
        sql: Original failed SQL
        error_msg: Validation error message
        question: Original sub-query question
        schema_info: Available schema context
        provider: LLM provider
        model: LLM model name

    Returns:
        Repaired SQL string, or None if repair fails
    """
    try:
        repair_prompt = f"""Fix the following SQL query that has a validation error.
Return ONLY the corrected SQL query, nothing else. No explanation, no markdown.

## Original Question
{question}

## Failed SQL
{sql}

## Error
{error_msg}

## Available Schema
{schema_info[:3000]}

## Rules
- Fix ONLY the error described above
- Do not change the query logic or intent
- Ensure all column references use correct table aliases
- Return a single SELECT statement
"""
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)
        response = await llm.ainvoke(repair_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        repaired = extract_sql_from_response(response_text)
        if repaired:
            logger.info(f"[ParallelSQL] LLM repair generated SQL ({len(repaired)} chars)")
        return repaired
    except Exception as e:
        logger.warning(f"[ParallelSQL] LLM repair failed: {e}")
        return None


async def _validate_sql(sql: str, market: str) -> tuple:
    """
    Validate SQL query: security check + table names + structure + EXPLAIN.

    Args:
        sql: SQL query string
        market: Market for table validation

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Security check
    is_safe, security_error = SQLTools.security_check(sql)
    if not is_safe:
        return False, f"Security violation: {security_error}"

    # SELECT-only check
    sql_stripped = sql.strip().upper()
    sql_check = sql_stripped.lstrip('(')
    if not (sql_check.startswith("SELECT") or sql_stripped.startswith("WITH")):
        return False, "Only SELECT statements are allowed"

    # Structural check
    structure_valid, structure_error = check_sql_structure(sql)
    if not structure_valid:
        return False, structure_error

    # Table name validation
    tables_valid, table_error, invalid_tables = validate_table_names(sql, market)
    if not tables_valid:
        return False, table_error

    # EXPLAIN validation
    is_valid, syntax_error = await validate_with_explain(sql)
    if not is_valid:
        return False, syntax_error

    return True, ""


async def _execute_sql(sql: str) -> tuple:
    """
    Execute SQL query and return results.

    Args:
        sql: Validated SQL query

    Returns:
        Tuple of (results_list, error_string_or_none)
    """
    if not db.pool:
        return [], "Database pool not available"

    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(sql)
            results = [dict(row) for row in rows]

            # Sort by date column if present (ASC for time-series)
            if results:
                date_columns = {"date", "trade_date", "trading_date"}
                date_col = next(
                    (k for k in results[0].keys() if k.lower() in date_columns),
                    None
                )
                if date_col:
                    results = sorted(
                        results,
                        key=lambda x: x.get(date_col) or ""
                    )

            return results, None
    except Exception as e:
        return [], str(e)


async def parallel_sql_pipeline(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute SQL pipeline for each sub-query in parallel.

    Strategy:
    1. Independent sub-queries (depends_on=None) run in parallel
    2. Dependent sub-queries run grouped by dependency level
    3. Results are merged with primary result for backward compatibility

    Args:
        state: Current graph state with sub_queries from query_decomposer

    Returns:
        Updated state with query_result, sub_query_results, generated_sql, etc.
    """
    logger.info("[AlphaAI:ParallelSQLPipeline] Processing...")

    sub_queries = state.get("sub_queries", [])
    message = state.get("message", "")
    entities = state.get("entities", {})
    provider = state.get("provider")
    model = state.get("model_name")
    messages = state.get("messages", [])

    if not sub_queries:
        logger.warning("[ParallelSQL] No sub-queries to execute")
        return {
            **state,
            "query_result": None,
            "result_count": 0,
            "generated_sql": None,
            "sql_valid": False,
            "sub_query_results": [],
            "processing_steps": state.get("processing_steps", []) + ["parallel_sql_pipeline"],
        }

    # Build conversation context
    conversation_context = ""
    if messages:
        conversation_context = format_conversation_context(messages)

    start_time = time.time()

    # === Safety net: merge independent screening sub-queries ===
    if len(sub_queries) >= 2:
        sub_queries = _maybe_merge_screening_subqueries(sub_queries, message)

    # === Phase 1: Execute independent sub-queries in parallel ===
    independent = [(i, sq) for i, sq in enumerate(sub_queries) if sq.get("depends_on") is None]
    dependent = [(i, sq) for i, sq in enumerate(sub_queries) if sq.get("depends_on") is not None]

    # Store results indexed by original position
    all_results = [None] * len(sub_queries)

    if independent:
        logger.info(f"[ParallelSQL] Executing {len(independent)} independent sub-queries in parallel")
        independent_tasks = [
            _execute_sub_query(
                sub_query=sq,
                message=message,
                entities=entities,
                provider=provider,
                model=model,
                conversation_context=conversation_context,
                sub_query_index=idx,
            )
            for idx, sq in independent
        ]
        independent_results = await asyncio.gather(*independent_tasks, return_exceptions=True)

        for (idx, _), result in zip(independent, independent_results):
            if isinstance(result, Exception):
                all_results[idx] = {
                    "question": sub_queries[idx]["question"],
                    "market": sub_queries[idx]["market"],
                    "tables": sub_queries[idx]["tables"],
                    "sql": None,
                    "result": [],
                    "result_count": 0,
                    "error": str(result),
                    "model_used": None,
                    "sub_query_index": idx,
                }
            else:
                all_results[idx] = result

    # === Phase 2: Execute dependent sub-queries by dependency level ===
    if dependent:
        # Group by dependency index
        dep_groups: Dict[int, List[tuple]] = {}
        for idx, sq in dependent:
            dep_idx = sq["depends_on"]
            dep_groups.setdefault(dep_idx, []).append((idx, sq))

        # Sort by dependency index to respect ordering
        for dep_idx in sorted(dep_groups.keys()):
            group = dep_groups[dep_idx]

            # Get dependency result
            dep_result_data = []
            if dep_idx is not None and dep_idx < len(all_results) and all_results[dep_idx]:
                dep_result_data = all_results[dep_idx].get("result", [])

            if not dep_result_data:
                # Dependency failed or returned empty (not due to empty intersection)
                # Merge parent's filter condition into dependent queries
                failed_parent = all_results[dep_idx] if dep_idx < len(all_results) else None
                parent_question = failed_parent.get("question", "") if failed_parent else ""
                parent_tables = failed_parent.get("tables", []) if failed_parent else []

                if parent_question:
                    for idx, sq in group:
                        sq["question"] = f"{parent_question} 조건을 포함하여, {sq['question']}"
                        sq["tables"] = list(set(sq.get("tables", []) + parent_tables))
                    logger.warning(
                        f"[ParallelSQL] Dependency {dep_idx} has no results, "
                        f"merged parent condition into {len(group)} dependent sub-queries: "
                        f"'{parent_question[:60]}'"
                    )
                else:
                    logger.warning(
                        f"[ParallelSQL] Dependency {dep_idx} has no results, "
                        f"executing {len(group)} dependent sub-queries without context"
                    )

            logger.info(
                f"[ParallelSQL] Executing {len(group)} dependent sub-queries "
                f"(depends_on={dep_idx}, dep_rows={len(dep_result_data)})"
            )

            dep_tasks = [
                _execute_sub_query(
                    sub_query=sq,
                    message=message,
                    entities=entities,
                    provider=provider,
                    model=model,
                    conversation_context=conversation_context,
                    dependency_result=dep_result_data,
                    sub_query_index=idx,
                )
                for idx, sq in group
            ]
            dep_results = await asyncio.gather(*dep_tasks, return_exceptions=True)

            for (idx, _), result in zip(group, dep_results):
                if isinstance(result, Exception):
                    all_results[idx] = {
                        "question": sub_queries[idx]["question"],
                        "market": sub_queries[idx]["market"],
                        "tables": sub_queries[idx]["tables"],
                        "sql": None,
                        "result": [],
                        "result_count": 0,
                        "error": str(result),
                        "model_used": None,
                        "sub_query_index": idx,
                    }
                else:
                    all_results[idx] = result

    total_time_ms = (time.time() - start_time) * 1000

    # === Result Merging ===
    # Filter out None entries (shouldn't happen but safety check)
    completed_results = [r for r in all_results if r is not None]

    # Determine primary result
    # Priority: last in dependency chain (most refined) > largest result set
    successful_results = [r for r in completed_results if r.get("result_count", 0) > 0]

    if successful_results:
        # Find deepest dependency chain result
        dep_depth = {}
        for i, sq in enumerate(sub_queries):
            depth = 0
            current = sq.get("depends_on")
            while current is not None and depth < 10:
                depth += 1
                current = sub_queries[current].get("depends_on") if current < len(sub_queries) else None
            dep_depth[i] = depth

        # Primary = sub-query with most dependents (the "pivot" others enrich from)
        # CTE screening: independent CTE (2 dependents) -> primary
        # Chain filter: filter step (5 dependents) -> primary
        dependent_count = {}
        for i in range(len(sub_queries)):
            dependent_count[i] = 0
        for i, sq in enumerate(sub_queries):
            dep = sq.get("depends_on")
            if dep is not None and dep in dependent_count:
                dependent_count[dep] += 1

        max_deps = 0
        pivot_result = None
        for r in successful_results:
            r_idx = r.get("sub_query_index", 0)
            deps = dependent_count.get(r_idx, 0)
            if deps > max_deps:
                max_deps = deps
                pivot_result = r

        if pivot_result:
            primary_result = pivot_result
        else:
            # No dependents at all (all independent): use deepest depth
            best_depth = -1
            primary_result = successful_results[0]
            for r in successful_results:
                r_idx = r.get("sub_query_index", 0)
                if dep_depth.get(r_idx, 0) > best_depth:
                    best_depth = dep_depth[r_idx]
                    primary_result = r
    elif completed_results:
        primary_result = completed_results[0]
    else:
        primary_result = {
            "question": message,
            "market": state.get("market", "KR"),
            "tables": [],
            "sql": None,
            "result": [],
            "result_count": 0,
            "error": "All sub-queries failed",
            "model_used": None,
        }

    # Collect all tables used
    all_tables_used = []
    for r in completed_results:
        for t in r.get("tables", []):
            if t not in all_tables_used:
                all_tables_used.append(t)

    # Build merged schema context
    merged_schema = await _build_schema_context(all_tables_used, state.get("market", "KR"))

    # Determine model used
    model_used = primary_result.get("model_used") or model or "unknown"

    # Log summary
    success_count = len(successful_results)
    fail_count = len(completed_results) - success_count
    total_rows = sum(r.get("result_count", 0) for r in completed_results)

    logger.info(
        f"[AlphaAI:ParallelSQLPipeline] Complete - "
        f"{success_count}/{len(completed_results)} succeeded, "
        f"{total_rows} total rows, {total_time_ms:.0f}ms"
    )

    if fail_count > 0:
        for r in completed_results:
            if r.get("error"):
                logger.warning(
                    f"[ParallelSQL] Failed: '{r['question'][:50]}' -> {r['error'][:100]}"
                )

    # === Update entities with actual stock names from SQL results ===
    # Priority: primary_result (deepest dependency chain, e.g. top5) first,
    # then remaining results. This ensures ExternalDataFetcher picks a
    # meaningful stock (e.g. SK Telecom) instead of a random SPAC.
    entities = state.get("entities") or {}
    if completed_results:
        ordered_names = []
        ordered_symbols = []
        seen_names = set()
        seen_symbols = set()

        # Phase 1: Extract from primary_result first
        for row in (primary_result.get("result") or []):
            if isinstance(row, dict):
                name = row.get("stock_name")
                symbol = row.get("symbol")
                if name and isinstance(name, str) and name not in seen_names:
                    seen_names.add(name)
                    ordered_names.append(name)
                if symbol and isinstance(symbol, str) and symbol not in seen_symbols:
                    seen_symbols.add(symbol)
                    ordered_symbols.append(symbol)

        # Phase 2: Add remaining stocks from other results
        for r in completed_results:
            if r is primary_result:
                continue
            for row in (r.get("result") or []):
                if isinstance(row, dict):
                    name = row.get("stock_name")
                    symbol = row.get("symbol")
                    if name and isinstance(name, str) and name not in seen_names:
                        seen_names.add(name)
                        ordered_names.append(name)
                    if symbol and isinstance(symbol, str) and symbol not in seen_symbols:
                        seen_symbols.add(symbol)
                        ordered_symbols.append(symbol)

        if ordered_names:
            entities = {**entities}
            entities["stock_names_from_sql"] = ordered_names
            if ordered_symbols:
                entities["stock_codes_from_sql"] = ordered_symbols
            logger.info(
                f"[ParallelSQL] Discovered {len(ordered_names)} stocks from SQL: "
                f"{ordered_names[:5]}"
            )

    # Track skipped/failed conditions for transparency
    skipped_conditions = []
    for r in completed_results:
        if r.get("error"):
            skipped_conditions.append({
                "sub_query_index": r.get("sub_query_index"),
                "question": r.get("question", ""),
                "error": r.get("error", "")[:150],
            })

    return {
        **state,
        # Backward-compatible fields (primary result)
        "query_result": primary_result["result"] if primary_result["result"] else None,
        "result_count": primary_result["result_count"],
        "generated_sql": primary_result.get("sql"),
        "sql_valid": primary_result["result_count"] > 0 or primary_result.get("sql") is not None,
        "execution_time_ms": total_time_ms,
        # Updated entities with SQL-discovered stocks
        "entities": entities,
        # New fields
        "sub_query_results": completed_results,
        "relevant_tables": all_tables_used,
        "schema_context": merged_schema,
        "sql_model_used": model_used,
        "primary_sub_query_question": primary_result.get("question", ""),
        "skipped_conditions": skipped_conditions,
        "processing_steps": state.get("processing_steps", []) + ["parallel_sql_pipeline"],
    }
