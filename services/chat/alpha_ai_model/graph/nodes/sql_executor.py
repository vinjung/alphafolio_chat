# services/chat/alpha_ai_model/graph/nodes/sql_executor.py
"""
SQL Execution Node

Executes validated SQL queries against PostgreSQL database.
Handles errors, timeouts, and result formatting.
"""
from typing import Dict, Any, List
from config import logger
from database import db
import time


async def sql_executor(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute SQL query against database

    Args:
        state: Current graph state with 'generated_sql' and 'sql_valid' fields

    Returns:
        Updated state with 'query_result', 'result_count', 'execution_time_ms'
    """
    logger.info("[AlphaAI:SQLExecutor] Processing...")

    generated_sql = state.get("generated_sql", "")
    sql_valid = state.get("sql_valid", False)

    # Skip if SQL is not valid
    if not sql_valid:
        logger.error("[AlphaAI:SQLExecutor] Skipping execution - SQL not valid")
        return {
            **state,
            "query_result": None,
            "result_count": 0,
            "execution_time_ms": 0,
            "processing_steps": state.get("processing_steps", []) + ["sql_executor"]
        }

    # Check database connection
    if not db.pool:
        logger.error("[AlphaAI:SQLExecutor] Database pool not available")
        return {
            **state,
            "query_result": None,
            "result_count": 0,
            "execution_time_ms": 0,
            "sql_error": "Database connection not available",
            "processing_steps": state.get("processing_steps", []) + ["sql_executor"]
        }

    try:
        start_time = time.time()

        async with db.pool.acquire() as conn:
            # Execute query
            rows = await conn.fetch(generated_sql)

            # Convert to list of dicts
            query_result: List[Dict[str, Any]] = [dict(row) for row in rows]
            result_count = len(query_result)

            # Sort time-series data by date ASC for all downstream nodes
            # (HybridAnalyzer, ResponseGenerator, chart visualization)
            if query_result:
                date_columns = {"date", "trade_date", "trading_date"}
                date_col = next(
                    (k for k in query_result[0].keys() if k.lower() in date_columns),
                    None
                )
                if date_col:
                    query_result = sorted(
                        query_result,
                        key=lambda x: x.get(date_col) or ""
                    )
                    logger.info(f"[SQLExecutor] Sorted {result_count} rows by '{date_col}' ASC")

        execution_time_ms = (time.time() - start_time) * 1000

        logger.info(f"[AlphaAI:SQLExecutor] Executed successfully: {result_count} rows in {execution_time_ms:.2f}ms")

        # Log result details for debugging
        if query_result:
            logger.debug(f"[SQLExecutor] Result columns: {list(query_result[0].keys())}")
            logger.debug(f"[SQLExecutor] First row sample: {query_result[0]}")

        # Detect empty result from fine-tuned model (Case B: valid SQL but 0 rows)
        empty_result_retry = False
        if (result_count == 0
                and (state.get("sql_model_used") or "").startswith("ft:")
                and state.get("sql_retry_count", 0) == 0):
            empty_result_retry = True
            logger.info("[SQLExecutor] Fine-tuned model returned 0 rows, will retry with Claude")

        return {
            **state,
            "query_result": query_result,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
            "empty_result_retry": empty_result_retry,
            "sql_retry_count": state.get("sql_retry_count", 0) + (1 if empty_result_retry else 0),
            "processing_steps": state.get("processing_steps", []) + ["sql_executor"]
        }

    except Exception as e:
        logger.error(f"[AlphaAI:SQLExecutor] Execution error: {str(e)}")
        return {
            **state,
            "query_result": None,
            "result_count": 0,
            "execution_time_ms": 0,
            "sql_error": str(e),
            "sql_valid": False,
            "processing_steps": state.get("processing_steps", []) + ["sql_executor"]
        }
