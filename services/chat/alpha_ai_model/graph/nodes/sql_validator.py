# services/chat/alpha_ai_model/graph/nodes/sql_validator.py
"""
SQL Validation Node

Validates generated SQL for:
- Syntax correctness (using EXPLAIN)
- Security (no dangerous keywords)
- Schema compliance
- Auto-retry with LLM on failure (up to 3 attempts)
"""
from typing import Dict, Any, Tuple, List, Set
import re
from config import logger
from database import db

from ...tools.sql_tools import SQLTools
from core.llm.factory import get_llm, LLMProvider


# Maximum retry attempts for SQL correction
MAX_RETRY_ATTEMPTS = 2

# Allowed tables by market
ALLOWED_KR_TABLES = {
    # Core price/quote tables
    'kr_intraday', 'kr_intraday_total', 'kr_intraday_detail',
    # Technical indicators
    'kr_indicators',
    # Quant analysis
    'kr_stock_grade',
    # Investor trading
    'kr_individual_investor_daily_trading', 'kr_investor_daily_trading', 'kr_program_daily_trading',
    # Stock information
    'kr_stock_basic', 'kr_stock_detail',
    # Trading data
    'kr_blocktrades', 'kr_foreign_ownership',
    # Financial data (DART)
    'kr_financial_position', 'kr_dividends', 'kr_largest_shareholder',
    'kr_stockacquisitiondisposal', 'kr_executive',
    # Research
    'kr_research_reports',
    # Benchmark/Sector
    'kr_benchmark_index', 'mv_sector_daily_performance',
    # Common tables
    'market_index', 'bok_economic_indicators', 'exchange_rate'
}

# SQL keywords/functions that regex may capture after FROM/JOIN but are NOT table names
SQL_KEYWORDS = {
    'lateral', 'unnest', 'generate_series', 'generate_subscripts',
    'json_each', 'jsonb_each', 'json_array_elements', 'jsonb_array_elements',
    'json_to_recordset', 'jsonb_to_recordset',
    'regexp_matches', 'regexp_split_to_table', 'string_to_table',
    'xmltable', 'rows', 'select', 'values', 'each',
    'information_schema', 'pg_catalog',
    # Date/time functions that appear after FROM in EXTRACT() expressions
    'current_date', 'current_timestamp', 'current_time',
    'localtime', 'localtimestamp', 'now',
}

ALLOWED_US_TABLES = {
    # Core price/quote tables
    'us_intraday', 'us_daily', 'us_daily_etf', 'us_weekly', 'us_monthly',
    # Technical indicators
    'us_indicators',
    # Stock information
    'us_stock_basic',
    # Quant analysis
    'us_stock_grade',
    # Options data
    'us_option', 'us_option_daily_summary',
    # IPO
    'us_ipo_calendar',
    # Financial statements
    'us_income_statement', 'us_balance_sheet', 'us_cash_flow',
    # Earnings
    'us_earnings_estimates', 'us_earnings_calendar',
    # Dividends and splits
    'us_dividends', 'us_splits',
    # News and insider
    'us_news', 'us_insider_transactions',
    # Macro/Economic indicators
    'us_fed_funds_rate', 'us_treasury_yield', 'us_cpi', 'us_unemployment_rate',
    'us_gdp', 'us_pmi',
    # Market regime and volatility
    'us_market_regime', 'us_vix', 'us_move_index', 'us_dollar_index',
    'us_credit_spread', 'us_fed_rrp',
    # Sector benchmarks
    'us_sector_benchmarks', 'mv_us_sector_daily_performance',
    # Common tables
    'market_index', 'bok_economic_indicators', 'exchange_rate'
}

# All real database tables start with one of these prefixes.
# Names without these prefixes (e.g., CTE aliases, subquery aliases) are skipped.
KNOWN_TABLE_PREFIXES = ('kr_', 'us_', 'market_', 'bok_', 'exchange_', 'mv_')


def extract_table_names(sql: str) -> Set[str]:
    """
    Extract table names from SQL query

    Args:
        sql: SQL query string

    Returns:
        Set of table names found in the query
    """
    # Patterns to match table names
    # FROM table_name, JOIN table_name, FROM table_name alias
    patterns = [
        r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
    ]

    tables = set()
    sql_upper = sql.upper()
    # Strip EXTRACT(... FROM ...) to avoid misdetecting column names as tables
    sql_for_extract = re.sub(r'EXTRACT\s*\([^)]*\)', '', sql, flags=re.IGNORECASE)

    for pattern in patterns:
        matches = re.findall(pattern, sql_for_extract, re.IGNORECASE)
        for match in matches:
            # Normalize to lowercase for comparison
            table_name = match.lower()
            if table_name not in SQL_KEYWORDS:
                tables.add(table_name)

    return tables


def extract_cte_names(sql: str) -> Set[str]:
    """
    Extract CTE (Common Table Expression) names from WITH clause

    Args:
        sql: SQL query string

    Returns:
        Set of CTE names defined in the query
    """
    cte_names = set()
    # Match: WITH name AS, WITH RECURSIVE name AS, or , name AS (for multiple CTEs)
    pattern = r'(?:WITH(?:\s+RECURSIVE)?\s+|,\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s+AS\s*\('
    matches = re.findall(pattern, sql, re.IGNORECASE)
    for match in matches:
        cte_names.add(match.lower())
    return cte_names


def check_sql_structure(sql: str) -> Tuple[bool, str]:
    """
    Check basic SQL structural integrity before expensive validation.
    Detects fundamentally broken SQL that should be fully regenerated.
    """
    # Check balanced parentheses
    depth = 0
    for char in sql:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        if depth < 0:
            return False, "Unbalanced parentheses: unexpected closing ')'"
    if depth != 0:
        return False, f"Unbalanced parentheses: {depth} unclosed '('"

    return True, ""


def validate_table_names(sql: str, market: str = "KR") -> Tuple[bool, str, List[str]]:
    """
    Validate that SQL only uses allowed table names

    Args:
        sql: SQL query string
        market: Market type (KR or US)

    Returns:
        Tuple of (is_valid, error_message, invalid_tables)
    """
    tables_in_sql = extract_table_names(sql)
    cte_names = extract_cte_names(sql)

    # Check if query uses tables from both markets (e.g., UNION queries)
    has_kr_tables = any(t.startswith('kr_') for t in tables_in_sql)
    has_us_tables = any(t.startswith('us_') for t in tables_in_sql)

    # Get allowed tables based on market
    if has_kr_tables and has_us_tables:
        # Combined query (e.g., UNION) - allow both markets
        allowed_tables = ALLOWED_KR_TABLES | ALLOWED_US_TABLES
    elif market == "BOTH":
        allowed_tables = ALLOWED_KR_TABLES | ALLOWED_US_TABLES
    elif market == "US":
        allowed_tables = ALLOWED_US_TABLES
    else:
        allowed_tables = ALLOWED_KR_TABLES

    # Find invalid tables (excluding CTE-defined names and non-table identifiers)
    invalid_tables = []
    for table in tables_in_sql:
        if table not in allowed_tables and table not in cte_names:
            # Only flag names with known table prefixes (kr_, us_, market_, etc.)
            # This avoids false positives from CTE aliases (max_year, ranked, etc.)
            if any(table.startswith(p) for p in KNOWN_TABLE_PREFIXES):
                invalid_tables.append(table)
            else:
                logger.debug(f"[SQLValidator] Ignoring non-table identifier: {table}")

    if invalid_tables:
        error_msg = f"Invalid table(s) used: {', '.join(invalid_tables)}. These tables do not exist in the database."
        logger.warning(f"[SQLValidator] {error_msg}")
        return False, error_msg, invalid_tables

    return True, "", []


# SQL correction prompt
SQL_CORRECTION_PROMPT = """The following SQL query has an error. Please fix it.

## Original SQL
```sql
{sql}
```

## Error Message
{error}

## Table Schema
{schema}

## Rules
1. Fix the syntax error based on the error message
2. Use only columns that exist in the schema
3. Keep the original query intent
4. Output only the corrected SQL, no explanation
5. Do not use columns or tables that don't exist

## Corrected SQL
```sql
"""


async def validate_with_explain(sql: str) -> Tuple[bool, str]:
    """
    Validate SQL syntax using EXPLAIN

    Args:
        sql: SQL query to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not db.pool:
        logger.warning("[SQLValidator] Database pool not available, skipping EXPLAIN validation")
        return True, ""

    try:
        async with db.pool.acquire() as conn:
            # Use EXPLAIN to validate syntax without executing
            await conn.execute(f"EXPLAIN {sql}")
        return True, ""
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"[SQLValidator] EXPLAIN validation failed: {error_msg}")
        return False, error_msg


async def fix_sql_with_llm(
    sql: str,
    error: str,
    schema: str,
    provider: str = None,
    model: str = None
) -> str:
    """
    Attempt to fix SQL using LLM

    Args:
        sql: Original SQL with error
        error: Error message
        schema: Relevant schema information
        provider: LLM provider
        model: Model name

    Returns:
        Fixed SQL string
    """
    try:
        llm_provider = LLMProvider(provider) if provider else LLMProvider.ANTHROPIC
        llm = get_llm(llm_provider, model_name=model)

        prompt = SQL_CORRECTION_PROMPT.format(
            sql=sql,
            error=error,
            schema=schema
        )

        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Extract SQL from response
        fixed_sql = extract_sql_from_response(response_text)

        if fixed_sql and fixed_sql != sql:
            logger.info(f"[SQLValidator] LLM proposed fix")
            return fixed_sql

        return sql

    except Exception as e:
        logger.error(f"[SQLValidator] LLM fix failed: {e}")
        return sql


def extract_sql_from_response(response: str) -> str:
    """
    Extract SQL from LLM response

    Args:
        response: Raw LLM response

    Returns:
        Cleaned SQL string
    """
    sql = response.strip()

    # Remove markdown code blocks
    if "```sql" in sql:
        sql = sql.split("```sql")[1]
        if "```" in sql:
            sql = sql.split("```")[0]
    elif "```" in sql:
        parts = sql.split("```")
        if len(parts) >= 2:
            sql = parts[1]

    # Clean up
    sql = sql.strip()

    # Remove trailing semicolons
    sql = sql.rstrip(';').strip()

    return sql


def get_common_fixes(sql: str, error: str) -> str:
    """
    Apply common fixes based on error patterns

    Args:
        sql: Original SQL
        error: Error message

    Returns:
        Fixed SQL or original if no fix applied
    """
    # Common error patterns and fixes
    error_lower = error.lower()

    # Column does not exist
    if "column" in error_lower and "does not exist" in error_lower:
        import re

        # Strategy 1: Use PostgreSQL HINT for alias-prefixed column errors
        # e.g., "column d.stock_name does not exist" + HINT: "i.stock_name"
        hint_match = re.search(
            r'perhaps you meant to reference the column "([^"]+)"', error_lower
        )
        if hint_match:
            correct_ref = hint_match.group(1)
            # Extract bad alias.column reference
            bad_ref_match = re.search(r'column (\w+\.\w+) does not exist', error_lower)
            if bad_ref_match:
                bad_ref = bad_ref_match.group(1)
                fixed_sql = sql.replace(bad_ref, correct_ref)
                logger.info(f"[SQLValidator] Applied HINT-based fix: {bad_ref} -> {correct_ref}")
                return fixed_sql

        # Strategy 2: Simple column name mapping
        match = re.search(r'column "(\w+)" does not exist', error_lower)
        if match:
            bad_column = match.group(1)

            # Common column name fixes
            fixes = {
                "trading_amount": "trading_value",
                "trade_value": "trading_value",
                "trade_volume": "volume",
                "mkt_cap": "market_cap",
                "marketcap": "market_cap",
                "price": "close",
                "name": "stock_name",
                # kr_largest_shareholder column hallucinations
                "major_shareholder_ratio": "trmend_posesn_stock_qota_rt",
                "shareholder_ratio": "trmend_posesn_stock_qota_rt",
                "ownership_ratio": "trmend_posesn_stock_qota_rt",
                "ownership_rate": "trmend_posesn_stock_qota_rt",
                "shareholder_name": "nm",
                "shareholder_nm": "nm",
                "shares_held": "trmend_posesn_stock_co",
                "beginning_shares": "bsis_posesn_stock_co",
                "beginning_ratio": "bsis_posesn_stock_qota_rt",
                "settlement_date": "stlm_dt",
                # Common pattern fixes
                "stock_code": "symbol",
                "ticker": "symbol",
                "company_name": "stock_name",
                "corp_nm": "corp_name",
            }

            if bad_column in fixes:
                fixed_sql = sql.replace(bad_column, fixes[bad_column])
                logger.info(f"[SQLValidator] Applied column fix: {bad_column} -> {fixes[bad_column]}")
                return fixed_sql

    # Table does not exist
    if "relation" in error_lower and "does not exist" in error_lower:
        import re
        match = re.search(r'relation "(\w+)" does not exist', error_lower)
        if match:
            bad_table = match.group(1)

            # Common table name fixes
            fixes = {
                "kr_daily": "kr_intraday_total",
                "us_intraday": "us_daily",
                "indicators": "kr_indicators",
                "stocks": "kr_intraday",
                # Cross-market hallucination fixes
                "us_stock_detail": "us_stock_basic",
                "us_intraday_total": "us_daily",
                "kr_daily_etf": "kr_intraday_total",
                "us_stock_info": "us_stock_basic",
                "kr_stock_info": "kr_stock_basic",
            }

            if bad_table in fixes:
                fixed_sql = sql.replace(bad_table, fixes[bad_table])
                logger.info(f"[SQLValidator] Applied table fix: {bad_table} -> {fixes[bad_table]}")
                return fixed_sql

    # Syntax errors
    if "syntax error" in error_lower:
        # Common syntax fixes
        if "near \"LIMIT\"" in error:
            # Might be missing ORDER BY before LIMIT
            pass

    return sql


async def sql_validator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate generated SQL query with auto-retry on failure

    Attempts to fix SQL errors using:
    1. Common pattern-based fixes
    2. LLM-based correction
    Up to MAX_RETRY_ATTEMPTS times

    Args:
        state: Current graph state with 'generated_sql' field

    Returns:
        Updated state with 'sql_valid', 'sql_error', and 'needs_regeneration' fields
    """
    logger.info("[AlphaAI:SQLValidator] Processing...")

    generated_sql = state.get("generated_sql", "")
    retry_count = state.get("sql_retry_count", 0)
    schema_context = state.get("schema_context", "")
    provider = state.get("provider")
    model = state.get("model_name")

    # Check if SQL exists
    if not generated_sql:
        logger.error("[AlphaAI:SQLValidator] No SQL to validate")
        return {
            **state,
            "sql_valid": False,
            "sql_error": "No SQL query generated",
            "needs_regeneration": False,
            "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
        }

    # Security check first
    is_safe, security_error = SQLTools.security_check(generated_sql)
    if not is_safe:
        logger.error(f"[AlphaAI:SQLValidator] Security check failed: {security_error}")
        return {
            **state,
            "sql_valid": False,
            "sql_error": f"Security violation: {security_error}",
            "needs_regeneration": False,
            "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
        }

    # Check if it's a SELECT statement
    sql_stripped = generated_sql.strip().upper()
    # Handle UNION queries that start with parentheses: (SELECT ...) UNION ALL (SELECT ...)
    sql_check = sql_stripped.lstrip('(')
    if not (sql_check.startswith("SELECT") or sql_stripped.startswith("WITH")):
        logger.error("[AlphaAI:SQLValidator] Only SELECT statements are allowed")
        # Respect retry count to prevent infinite loops
        should_retry = retry_count < MAX_RETRY_ATTEMPTS
        if not should_retry:
            logger.error(f"[AlphaAI:SQLValidator] Max retries ({MAX_RETRY_ATTEMPTS}) reached for non-SELECT output")
        return {
            **state,
            "sql_valid": False,
            "sql_error": "Only SELECT statements are allowed" if should_retry else "Unable to generate valid SQL query for this question",
            "needs_regeneration": should_retry,
            "sql_retry_count": retry_count + 1,
            "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
        }

    # Structural validation (catch fundamentally broken SQL early)
    structure_valid, structure_error = check_sql_structure(generated_sql)
    if not structure_valid:
        logger.warning(f"[AlphaAI:SQLValidator] Structural check failed: {structure_error}")
        should_retry = retry_count < MAX_RETRY_ATTEMPTS
        return {
            **state,
            "sql_valid": False,
            "sql_error": structure_error,
            "needs_regeneration": should_retry,
            "sql_retry_count": retry_count + 1,
            "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
        }

    # Validate table names (prevent hallucinated tables)
    market = state.get("market", "KR")
    tables_valid, table_error, invalid_tables = validate_table_names(generated_sql, market)
    if not tables_valid:
        logger.error(f"[AlphaAI:SQLValidator] Invalid tables detected: {invalid_tables}")
        should_retry = retry_count < MAX_RETRY_ATTEMPTS
        return {
            **state,
            "sql_valid": False,
            "sql_error": table_error,
            "needs_regeneration": should_retry,
            "sql_retry_count": retry_count + 1,
            "invalid_tables": invalid_tables,
            "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
        }

    # Validate syntax with EXPLAIN
    current_sql = generated_sql
    is_valid, syntax_error = await validate_with_explain(current_sql)

    # If invalid, try to fix
    if not is_valid and retry_count < MAX_RETRY_ATTEMPTS:
        logger.info(f"[SQLValidator] Attempting fix (attempt {retry_count + 1}/{MAX_RETRY_ATTEMPTS})")

        # Try common fixes first
        fixed_sql = get_common_fixes(current_sql, syntax_error)

        if fixed_sql != current_sql:
            # Validate the fix
            is_valid, syntax_error = await validate_with_explain(fixed_sql)
            if is_valid:
                current_sql = fixed_sql
                logger.info("[SQLValidator] Common fix successful")

        # If still invalid, try LLM fix
        if not is_valid:
            fixed_sql = await fix_sql_with_llm(
                current_sql,
                syntax_error,
                schema_context,
                provider,
                model
            )

            if fixed_sql != current_sql:
                is_valid, new_error = await validate_with_explain(fixed_sql)
                if is_valid:
                    current_sql = fixed_sql
                    syntax_error = ""
                    logger.info("[SQLValidator] LLM fix successful")
                else:
                    syntax_error = new_error

    if is_valid:
        logger.info("[AlphaAI:SQLValidator] SQL validation passed")
        return {
            **state,
            "generated_sql": current_sql,  # Use potentially fixed SQL
            "sql_valid": True,
            "sql_error": None,
            "needs_regeneration": False,
            "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
        }
    else:
        # Validation failed
        logger.warning(f"[AlphaAI:SQLValidator] Validation failed: {syntax_error}")

        # Check if we should retry with full regeneration
        if retry_count < MAX_RETRY_ATTEMPTS:
            logger.info(f"[AlphaAI:SQLValidator] Will regenerate SQL (attempt {retry_count + 1})")
            return {
                **state,
                "sql_valid": False,
                "sql_error": syntax_error,
                "needs_regeneration": True,
                "sql_retry_count": retry_count + 1,
                "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
            }
        else:
            logger.error(f"[AlphaAI:SQLValidator] Max retries reached, SQL invalid")
            return {
                **state,
                "sql_valid": False,
                "sql_error": f"SQL validation failed after {MAX_RETRY_ATTEMPTS} attempts: {syntax_error}",
                "needs_regeneration": False,
                "processing_steps": state.get("processing_steps", []) + ["sql_validator"]
            }
