#!/usr/bin/env python3
# fine_tuning/generate_synthetic_data.py
"""
Synthetic Training Data Generator

Uses Claude (Anthropic API) to generate synthetic training data from
the existing 156 few-shot examples. Targets 500-1000 total examples
via three generation strategies:

1. Paraphrase (~250): Same SQL, different question phrasing
2. Parameter Variation (~150): Same pattern, different parameters
3. Novel Complex (~100): New multi-JOIN, CTE, window function queries

Each generated SQL is validated via EXPLAIN on PostgreSQL (asyncpg).
Output is JSONL compatible with OpenAI fine-tuning chat format.
"""

import sys
import os
import json
import asyncio
import argparse
import logging
import random
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to sys.path for imports
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fine_tuning.config import (
    SYSTEM_MESSAGE,
    DATA_DIR,
    SYNTHETIC_DATA_PATH,
    PARAPHRASE_TARGET,
    PARAMETER_VARIATION_TARGET,
    NOVEL_COMPLEX_TARGET,
    GENERATION_BATCH_SIZE,
    DATABASE_URL,
)
from services.chat.alpha_ai_model.prompts.sql_prompt import (
    ALL_SCHEMAS,
    TERM_MAPPING_TEXT,
)
from services.chat.alpha_ai_model.prompts.few_shot_examples import FEW_SHOT_EXAMPLES

import anthropic
import asyncpg

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CLAUDE_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 8192
# Number of alternative phrasings per source example
PARAPHRASES_PER_EXAMPLE = 3
# Number of parameter variations per source example
VARIATIONS_PER_EXAMPLE = 3
# Retry / rate-limit settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


# ============================================================================
# SQL Validation
# ============================================================================

async def validate_sql(sql: str, pool: asyncpg.Pool) -> bool:
    """
    Validate a SQL query using PostgreSQL EXPLAIN.

    Runs EXPLAIN (not EXPLAIN ANALYZE) so the query is parsed and planned
    but never actually executed. Returns True if the SQL is syntactically
    and semantically valid against the live schema.

    Args:
        sql: The SQL query string to validate.
        pool: An asyncpg connection pool.

    Returns:
        True if EXPLAIN succeeds, False otherwise.
    """
    # Strip trailing semicolons and whitespace for safety
    sql_clean = sql.strip().rstrip(";").strip()
    if not sql_clean:
        return False

    # Reject non-SELECT statements
    first_keyword = sql_clean.split()[0].upper() if sql_clean.split() else ""
    if first_keyword not in ("SELECT", "WITH"):
        logger.warning("Rejected non-SELECT statement starting with: %s", first_keyword)
        return False

    try:
        async with pool.acquire() as conn:
            await conn.execute(f"EXPLAIN {sql_clean}")
        return True
    except Exception as exc:
        logger.debug("EXPLAIN failed: %s | SQL: %.120s", exc, sql_clean)
        return False


# ============================================================================
# Helpers
# ============================================================================

def _extract_json_array(text: str) -> Optional[list]:
    """
    Extract the first JSON array from a text response.

    Claude may wrap the JSON in markdown code fences or add commentary.
    This function tries several strategies to locate and parse the array.
    """
    # Try direct parse first
    text = text.strip()
    if text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Try to extract from markdown code block
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find array boundaries
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _call_claude(client: anthropic.Anthropic, prompt: str) -> str:
    """
    Call the Claude API with retry logic.

    Args:
        client: Anthropic client instance.
        prompt: The user message to send.

    Returns:
        The assistant's text response.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY_SECONDS * attempt
                logger.warning("Rate limited. Retrying in %ds (attempt %d/%d)", delay, attempt, MAX_RETRIES)
                time.sleep(delay)
            else:
                raise
        except anthropic.APIError as exc:
            if attempt < MAX_RETRIES:
                logger.warning("API error: %s. Retrying (attempt %d/%d)", exc, attempt, MAX_RETRIES)
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                raise
    return ""


def _format_training_example(question: str, sql: str) -> Dict[str, Any]:
    """
    Format a question-SQL pair into the OpenAI fine-tuning JSONL structure.

    Uses the same schema-enriched format as prepare_training_data.py:
    - Extracts table names from SQL
    - Builds relevant schema for those tables
    - Constructs user message: ## Database Schema + ## Term Mapping + ## Question

    Returns a dict with the chat messages format:
    {"messages": [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": "## Database Schema\\n...\\n## Term Mapping\\n...\\n## Question\\n..."},
        {"role": "assistant", "content": sql}
    ]}
    """
    from fine_tuning.prepare_training_data import (
        extract_tables_from_sql,
        get_relevant_schema,
        clean_sql,
    )

    # Extract tables used in this SQL
    known_tables = list(ALL_SCHEMAS.keys())
    tables_used = extract_tables_from_sql(sql, known_tables)

    # Build relevant schema (only tables used in the query)
    relevant_schema = get_relevant_schema(tables_used)
    if not relevant_schema:
        relevant_schema = "(No specific table schema matched)"

    # Build user message content with schema format
    user_content = (
        f"## Database Schema\n{relevant_schema}\n\n"
        f"## Term Mapping\n{TERM_MAPPING_TEXT.strip()}\n\n"
        f"## Question\n{question}"
    )

    # Clean the SQL for assistant output
    cleaned_sql = clean_sql(sql)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": cleaned_sql},
        ]
    }


# ============================================================================
# Strategy 1: Paraphrase Generation
# ============================================================================

async def generate_paraphrases(
    examples: List[Dict[str, str]],
    client: anthropic.Anthropic,
    pool: asyncpg.Pool,
) -> List[Dict[str, Any]]:
    """
    Generate paraphrased questions for existing SQL answers.

    For each source example, ask Claude to produce alternative Korean
    question phrasings that map to the same SQL query. Validates the
    original SQL via EXPLAIN to ensure we only paraphrase valid examples.

    Args:
        examples: Source examples from FEW_SHOT_EXAMPLES.
        client: Anthropic API client.
        pool: asyncpg connection pool for SQL validation.

    Returns:
        List of training examples in JSONL-ready format.
    """
    results: List[Dict[str, Any]] = []
    total_needed = PARAPHRASE_TARGET
    # Shuffle to get variety if we hit the target early
    shuffled = list(examples)
    random.shuffle(shuffled)

    logger.info("=== Strategy 1: Paraphrase Generation (target: %d) ===", total_needed)
    processed = 0
    skipped_invalid = 0

    for batch_start in range(0, len(shuffled), GENERATION_BATCH_SIZE):
        if len(results) >= total_needed:
            break

        batch = shuffled[batch_start : batch_start + GENERATION_BATCH_SIZE]

        for example in batch:
            if len(results) >= total_needed:
                break

            question = example["question"]
            sql = example["sql"]

            # Validate the original SQL first
            is_valid = await validate_sql(sql, pool)
            if not is_valid:
                skipped_invalid += 1
                logger.debug("Skipping invalid source SQL: %.80s", sql)
                continue

            prompt = (
                "You are a Korean financial data analyst. "
                "Given the following SQL query and its corresponding Korean question, "
                f"generate {PARAPHRASES_PER_EXAMPLE} alternative phrasings of the question "
                "in Korean that would produce the exact same SQL query. "
                "The alternative phrasings should vary in formality, wording, and structure "
                "but must convey the same data request.\n\n"
                f"Original question: {question}\n"
                f"SQL query: {sql}\n\n"
                f"Return a JSON array of {PARAPHRASES_PER_EXAMPLE} strings (Korean questions only). "
                "No explanation, no markdown -- just the raw JSON array."
            )

            try:
                response_text = _call_claude(client, prompt)
                paraphrases = _extract_json_array(response_text)

                if paraphrases and isinstance(paraphrases, list):
                    for alt_question in paraphrases:
                        if isinstance(alt_question, str) and alt_question.strip():
                            results.append(_format_training_example(alt_question.strip(), sql))
                            if len(results) >= total_needed:
                                break
                else:
                    logger.warning("Failed to parse paraphrases for: %.60s", question)

            except Exception as exc:
                logger.error("Error generating paraphrases for '%.60s': %s", question, exc)

            processed += 1
            if processed % 10 == 0:
                logger.info("  Paraphrase progress: %d/%d generated, %d examples processed",
                            len(results), total_needed, processed)

    logger.info("Paraphrase generation complete: %d examples (skipped %d invalid source SQLs)",
                len(results), skipped_invalid)
    return results


# ============================================================================
# Strategy 2: Parameter Variation Generation
# ============================================================================

async def generate_parameter_variations(
    examples: List[Dict[str, str]],
    client: anthropic.Anthropic,
    pool: asyncpg.Pool,
) -> List[Dict[str, Any]]:
    """
    Generate parameter variations of existing SQL patterns.

    For each source example, ask Claude to produce variations with
    different stock codes, LIMIT values, threshold parameters, date
    ranges, etc. Each variation is validated via EXPLAIN.

    Args:
        examples: Source examples from FEW_SHOT_EXAMPLES.
        client: Anthropic API client.
        pool: asyncpg connection pool for SQL validation.

    Returns:
        List of training examples in JSONL-ready format.
    """
    results: List[Dict[str, Any]] = []
    total_needed = PARAMETER_VARIATION_TARGET
    shuffled = list(examples)
    random.shuffle(shuffled)

    logger.info("=== Strategy 2: Parameter Variation (target: %d) ===", total_needed)
    processed = 0
    validated = 0
    rejected = 0

    for batch_start in range(0, len(shuffled), GENERATION_BATCH_SIZE):
        if len(results) >= total_needed:
            break

        batch = shuffled[batch_start : batch_start + GENERATION_BATCH_SIZE]

        for example in batch:
            if len(results) >= total_needed:
                break

            question = example["question"]
            sql = example["sql"]
            market = example.get("market", "KR")

            prompt = (
                "You are a Korean financial data analyst and PostgreSQL expert. "
                "Given the following SQL query pattern and its Korean question, "
                f"generate {VARIATIONS_PER_EXAMPLE} variations with different parameters. "
                "Change stock codes/tickers, LIMIT values, numeric thresholds, "
                "date intervals, or filter conditions while keeping the same query structure.\n\n"
                f"Market: {market}\n"
                f"Original question: {question}\n"
                f"Original SQL: {sql}\n\n"
                "For Korean stocks, use real stock codes like: "
                "'005930' (Samsung), '000660' (SK Hynix), '035420' (Naver), "
                "'035720' (Kakao), '005380' (Hyundai Motor), '051910' (LG Chem), "
                "'006400' (Samsung SDI), '003670' (Posco), '068270' (Celltrion), "
                "'005490' (POSCO Holdings).\n"
                "For US stocks, use real tickers like: "
                "'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'NFLX'.\n\n"
                f"Return a JSON array of {VARIATIONS_PER_EXAMPLE} objects, each with "
                '"question" (Korean) and "sql" (PostgreSQL) keys. '
                "No explanation, no markdown -- just the raw JSON array."
            )

            try:
                response_text = _call_claude(client, prompt)
                variations = _extract_json_array(response_text)

                if variations and isinstance(variations, list):
                    for var in variations:
                        if (
                            isinstance(var, dict)
                            and "question" in var
                            and "sql" in var
                            and isinstance(var["question"], str)
                            and isinstance(var["sql"], str)
                        ):
                            is_valid = await validate_sql(var["sql"], pool)
                            if is_valid:
                                results.append(
                                    _format_training_example(
                                        var["question"].strip(),
                                        var["sql"].strip(),
                                    )
                                )
                                validated += 1
                            else:
                                rejected += 1

                            if len(results) >= total_needed:
                                break
                else:
                    logger.warning("Failed to parse variations for: %.60s", question)

            except Exception as exc:
                logger.error("Error generating variations for '%.60s': %s", question, exc)

            processed += 1
            if processed % 10 == 0:
                logger.info("  Variation progress: %d/%d generated, %d validated, %d rejected",
                            len(results), total_needed, validated, rejected)

    logger.info("Parameter variation complete: %d examples (validated: %d, rejected: %d)",
                len(results), validated, rejected)
    return results


# ============================================================================
# Strategy 3: Novel Complex Query Generation
# ============================================================================

async def generate_novel_complex(
    schemas: Dict[str, str],
    client: anthropic.Anthropic,
    pool: asyncpg.Pool,
) -> List[Dict[str, Any]]:
    """
    Generate novel complex analytical SQL queries.

    Provides Claude with the full database schema and asks it to create
    complex queries using multi-JOIN, CTEs, window functions, subqueries,
    and advanced aggregations. Each query is validated via EXPLAIN.

    Args:
        schemas: Dictionary of table_name -> schema_text from ALL_SCHEMAS.
        client: Anthropic API client.
        pool: asyncpg connection pool for SQL validation.

    Returns:
        List of training examples in JSONL-ready format.
    """
    results: List[Dict[str, Any]] = []
    total_needed = NOVEL_COMPLEX_TARGET

    logger.info("=== Strategy 3: Novel Complex Queries (target: %d) ===", total_needed)
    validated = 0
    rejected = 0

    # Define categories of complex queries to generate
    complexity_categories = [
        {
            "name": "multi_join_kr",
            "description": (
                "Multi-JOIN queries for Korean stocks combining 3+ tables. "
                "Examples: price data + technical indicators + quant grades, "
                "or price data + investor trading + foreign ownership."
            ),
            "focus_tables": "kr_intraday_total, kr_indicators, kr_stock_grade, "
                            "kr_individual_investor_daily_trading, kr_foreign_ownership, "
                            "kr_stock_basic, kr_stock_detail",
        },
        {
            "name": "cte_analytical_kr",
            "description": (
                "CTE (WITH clause) queries for Korean stocks. "
                "Examples: find stocks where foreign buying increased for 5 consecutive days, "
                "or calculate rolling averages and compare with current values."
            ),
            "focus_tables": "kr_intraday_total, kr_indicators, kr_individual_investor_daily_trading, "
                            "kr_stock_grade",
        },
        {
            "name": "window_function_kr",
            "description": (
                "Window function queries for Korean stocks. "
                "Examples: rank stocks by daily return within each sector, "
                "calculate running totals of institutional net buying, "
                "or find stocks with N-day price momentum above market average."
            ),
            "focus_tables": "kr_intraday_total, kr_indicators, kr_stock_grade, "
                            "kr_individual_investor_daily_trading",
        },
        {
            "name": "multi_join_us",
            "description": (
                "Multi-JOIN queries for US stocks combining 3+ tables. "
                "Examples: daily price + indicators + stock fundamentals, "
                "or earnings estimates + income statement + balance sheet."
            ),
            "focus_tables": "us_daily, us_indicators, us_stock_basic, us_stock_grade, "
                            "us_income_statement, us_balance_sheet, us_cash_flow, "
                            "us_earnings_estimates",
        },
        {
            "name": "cte_analytical_us",
            "description": (
                "CTE queries for US stocks. "
                "Examples: identify stocks with improving earnings estimates over 3 quarters, "
                "or find options with unusual volume relative to open interest."
            ),
            "focus_tables": "us_daily, us_indicators, us_stock_basic, us_stock_grade, "
                            "us_earnings_estimates, us_option_daily_summary",
        },
        {
            "name": "cross_market",
            "description": (
                "UNION ALL queries comparing Korean and US markets. "
                "Examples: compare top RSI stocks across both markets, "
                "or find best quant-graded stocks in both KR and US."
            ),
            "focus_tables": "kr_intraday_total, kr_indicators, kr_stock_grade, "
                            "us_daily, us_indicators, us_stock_grade",
        },
        {
            "name": "macro_correlation",
            "description": (
                "Queries combining market/economic data with stock data. "
                "Examples: compare VIX levels with stock volatility, "
                "or analyze sector performance during different Fed rate environments."
            ),
            "focus_tables": "market_index, us_vix, us_fed_funds_rate, us_treasury_yield, "
                            "us_cpi, bok_economic_indicators, us_sector_benchmarks",
        },
    ]

    queries_per_batch = 5
    max_rounds_per_category = 3

    for category in complexity_categories:
        if len(results) >= total_needed:
            break

        # Build schema with only focus_tables for this category
        focus_table_names = [t.strip() for t in category["focus_tables"].split(",")]
        schema_parts = []
        for table_name in focus_table_names:
            if table_name in schemas:
                schema_parts.append(schemas[table_name].strip())
        focus_schema = "\n\n".join(schema_parts)

        for round_num in range(max_rounds_per_category):
            if len(results) >= total_needed:
                break

            prompt = (
                "You are a PostgreSQL expert for Korean and US financial stock data analysis. "
                "Generate complex analytical SQL queries with corresponding Korean questions.\n\n"
                f"## Task\nGenerate {queries_per_batch} complex {category['description']}\n\n"
                f"## Focus Tables\n{category['focus_tables']}\n\n"
                f"## Database Schema\n{focus_schema}\n\n"
                f"## Term Mapping\n{TERM_MAPPING_TEXT}\n\n"
                "## Requirements\n"
                "- Each query MUST be a valid PostgreSQL SELECT statement\n"
                "- Use real techniques: CTEs (WITH), window functions (ROW_NUMBER, RANK, LAG, LEAD), "
                "CASE WHEN, complex JOINs, subqueries, aggregations\n"
                "- Questions MUST be in Korean and represent realistic analytical questions\n"
                "- Use MAX(date) subquery pattern for latest data (never CURRENT_DATE)\n"
                "- For Korean stocks use real codes: '005930', '000660', '035420', '035720', '005380'\n"
                "- For US stocks use real tickers: 'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'\n"
                "- kr_intraday has NO date column; use kr_intraday_total for date-based queries\n"
                "- us_stock_detail does NOT exist; use us_stock_basic for US stock info\n"
                "- Output ONLY SELECT statements\n\n"
                f"Return a JSON array of {queries_per_batch} objects, each with "
                '"question" (Korean) and "sql" (PostgreSQL) keys. '
                "No explanation, no markdown -- just the raw JSON array."
            )

            try:
                response_text = _call_claude(client, prompt)
                novel_queries = _extract_json_array(response_text)

                if novel_queries and isinstance(novel_queries, list):
                    for item in novel_queries:
                        if len(results) >= total_needed:
                            break

                        if (
                            isinstance(item, dict)
                            and "question" in item
                            and "sql" in item
                            and isinstance(item["question"], str)
                            and isinstance(item["sql"], str)
                        ):
                            is_valid = await validate_sql(item["sql"], pool)
                            if is_valid:
                                results.append(
                                    _format_training_example(
                                        item["question"].strip(),
                                        item["sql"].strip(),
                                    )
                                )
                                validated += 1
                            else:
                                rejected += 1
                                logger.debug(
                                    "Rejected invalid novel SQL (category=%s): %.120s",
                                    category["name"],
                                    item["sql"],
                                )
                else:
                    logger.warning("Failed to parse novel queries for category: %s (round %d)",
                                   category["name"], round_num + 1)

            except Exception as exc:
                logger.error("Error generating novel queries (category=%s, round %d): %s",
                             category["name"], round_num + 1, exc)

            logger.info("  Novel [%s] round %d: %d total so far (%d validated, %d rejected)",
                         category["name"], round_num + 1, len(results), validated, rejected)

    logger.info("Novel complex generation complete: %d examples (validated: %d, rejected: %d)",
                len(results), validated, rejected)
    return results


# ============================================================================
# Main Orchestrator
# ============================================================================

async def main() -> None:
    """
    Orchestrate all three synthetic data generation strategies.

    1. Connect to PostgreSQL via asyncpg for SQL validation.
    2. Initialize Anthropic client for Claude API calls.
    3. Run each strategy sequentially.
    4. Merge results and write to JSONL output file.
    5. Print generation statistics.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic SQL training data using Claude"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(SYNTHETIC_DATA_PATH),
        help=f"Output JSONL file path (default: {SYNTHETIC_DATA_PATH})",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=DATABASE_URL,
        help="PostgreSQL connection URL (default: from DATABASE_URL env var)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip SQL EXPLAIN validation (useful for dry runs without DB access)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    args = parser.parse_args()

    random.seed(args.seed)

    output_path = Path(args.output)
    database_url = args.database_url

    if not database_url and not args.skip_validation:
        logger.error(
            "DATABASE_URL is not set and --skip-validation is not enabled. "
            "Set DATABASE_URL environment variable or use --skip-validation."
        )
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize Anthropic client
    client = anthropic.Anthropic()
    logger.info("Anthropic client initialized (model: %s)", CLAUDE_MODEL)

    # Connect to PostgreSQL for EXPLAIN validation
    pool: Optional[asyncpg.Pool] = None
    if not args.skip_validation:
        logger.info("Connecting to PostgreSQL for SQL validation...")
        try:
            pool = await asyncpg.create_pool(database_url, min_size=2, max_size=5)
            # Verify connectivity
            async with pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                logger.info("Connected to PostgreSQL: %.80s", version)
        except Exception as exc:
            logger.error("Failed to connect to PostgreSQL: %s", exc)
            sys.exit(1)
    else:
        logger.warning("SQL validation is DISABLED (--skip-validation). "
                        "Generated SQL may contain errors.")

    # Create a dummy pool wrapper when validation is skipped
    class _DummyPool:
        """Dummy pool that always validates SQL as True when validation is skipped."""

        class _DummyConn:
            async def execute(self, _sql: str) -> None:
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        def acquire(self):
            return self._DummyConn()

    validation_pool = pool if pool is not None else _DummyPool()

    try:
        # ---------------------------------------------------------------
        # Run generation strategies
        # ---------------------------------------------------------------
        all_results: List[Dict[str, Any]] = []

        # Strategy 1: Paraphrases
        paraphrase_results = await generate_paraphrases(
            FEW_SHOT_EXAMPLES, client, validation_pool
        )
        all_results.extend(paraphrase_results)

        # Strategy 2: Parameter Variations
        variation_results = await generate_parameter_variations(
            FEW_SHOT_EXAMPLES, client, validation_pool
        )
        all_results.extend(variation_results)

        # Strategy 3: Novel Complex Queries
        novel_results = await generate_novel_complex(
            ALL_SCHEMAS, client, validation_pool
        )
        all_results.extend(novel_results)

        # ---------------------------------------------------------------
        # Deduplicate by (question, sql) pair
        # ---------------------------------------------------------------
        seen = set()
        unique_results = []
        for item in all_results:
            msgs = item["messages"]
            key = (msgs[1]["content"], msgs[2]["content"])
            if key not in seen:
                seen.add(key)
                unique_results.append(item)

        duplicates_removed = len(all_results) - len(unique_results)

        # ---------------------------------------------------------------
        # Write JSONL output
        # ---------------------------------------------------------------
        with open(output_path, "w", encoding="utf-8") as f:
            for item in unique_results:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        logger.info("Output written to: %s", output_path)

        # ---------------------------------------------------------------
        # Print statistics
        # ---------------------------------------------------------------
        print("\n" + "=" * 60)
        print("  Synthetic Data Generation - Summary")
        print("=" * 60)
        print(f"  Source examples:           {len(FEW_SHOT_EXAMPLES)}")
        print(f"  Strategy 1 (Paraphrase):   {len(paraphrase_results)} / {PARAPHRASE_TARGET} target")
        print(f"  Strategy 2 (Variation):    {len(variation_results)} / {PARAMETER_VARIATION_TARGET} target")
        print(f"  Strategy 3 (Novel):        {len(novel_results)} / {NOVEL_COMPLEX_TARGET} target")
        print(f"  Duplicates removed:        {duplicates_removed}")
        print(f"  Total unique generated:    {len(unique_results)}")
        total_with_original = len(FEW_SHOT_EXAMPLES) + len(unique_results)
        print(f"  Grand total (w/ original): {total_with_original}")
        print(f"  Output file:               {output_path}")
        print("=" * 60 + "\n")

        if total_with_original < 500:
            logger.warning(
                "Total examples (%d) is below the 500 minimum target. "
                "Consider re-running or adjusting generation parameters.",
                total_with_original,
            )

    finally:
        if pool is not None:
            await pool.close()
            logger.info("PostgreSQL connection pool closed.")


if __name__ == "__main__":
    asyncio.run(main())
