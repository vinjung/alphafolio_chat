# fine_tuning/evaluate.py
"""
SQL Generation Model Evaluation

Evaluates and compares SQL generation quality across three model configurations:
  A: Claude Sonnet 4 + full prompt (current production)
  B: Fine-tuned gpt-4o-mini + simplified prompt
  C: Base gpt-4o-mini + full prompt (control)

Metrics: SQL validity (EXPLAIN pass rate), result accuracy, latency,
token usage, and estimated cost per query.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path for cross-package imports
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import asyncio
import asyncpg
import anthropic
import openai
import json
import time
import argparse
from copy import deepcopy
from typing import Dict, List, Optional, Tuple, Any

from fine_tuning.config import (
    TEST_SET_PATH,
    EVAL_CONFIGS,
    DEPLOYMENT_THRESHOLDS,
    DATABASE_URL,
    EVALUATION_RESULTS_PATH,
    SYSTEM_MESSAGE,
)
from services.chat.alpha_ai_model.prompts.sql_prompt import (
    ALL_SCHEMAS,
    TERM_MAPPING_TEXT,
    get_sql_prompt,
)
from services.chat.alpha_ai_model.prompts.sql_prompt_finetuned import (
    get_finetuned_sql_prompt,
)


# ---------------------------------------------------------------------------
# Cost tables (USD per 1K tokens, as of 2025-Q2)
# ---------------------------------------------------------------------------
COST_TABLE: Dict[str, Dict[str, float]] = {
    # Anthropic
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    # OpenAI
    "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
    # Fine-tuned gpt-4o-mini (training cost not included here)
    "gpt-4o-mini-ft": {"input": 0.000300, "output": 0.001200},
    # GPT-4.1 family
    "gpt-4.1-nano": {"input": 0.000100, "output": 0.000400},
    "gpt-4.1-mini": {"input": 0.000400, "output": 0.001600},
    "gpt-4.1": {"input": 0.002000, "output": 0.008000},
    # Fine-tuned gpt-4.1-mini (base 2x pricing)
    "gpt-4.1-mini-ft": {"input": 0.000800, "output": 0.003200},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a single API call."""
    # Try exact match first, then prefix match for fine-tuned model IDs
    costs = COST_TABLE.get(model)
    if costs is None:
        for prefix, c in COST_TABLE.items():
            if model.startswith(prefix):
                costs = c
                break
    if costs is None:
        return 0.0
    return (input_tokens / 1000.0) * costs["input"] + (output_tokens / 1000.0) * costs["output"]


# ---------------------------------------------------------------------------
# SQL validation and execution
# ---------------------------------------------------------------------------

async def validate_sql(sql: str, pool: asyncpg.Pool) -> bool:
    """
    Validate SQL syntax and semantics by running EXPLAIN.

    Returns True if the query plan is successfully generated,
    False otherwise (syntax error, missing table/column, etc.).
    """
    if not sql or not sql.strip():
        return False
    try:
        async with pool.acquire() as conn:
            await conn.execute(f"EXPLAIN {sql}")
        return True
    except Exception:
        return False


async def execute_sql(sql: str, pool: asyncpg.Pool) -> Optional[List[dict]]:
    """
    Execute SQL and return results as a list of dicts.

    Returns None on failure (timeout, error, etc.).
    Applies a 30-second statement timeout to prevent runaway queries.
    """
    if not sql or not sql.strip():
        return None
    try:
        async with pool.acquire() as conn:
            await conn.execute("SET statement_timeout = '30s'")
            rows = await conn.fetch(sql)
            return [dict(row) for row in rows]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# SQL generation per config
# ---------------------------------------------------------------------------

def _build_full_prompt_schema() -> str:
    """Combine all schemas into a single string for the full prompt."""
    return "\n".join(ALL_SCHEMAS.values())


async def generate_sql_with_config(
    config: dict,
    question: str,
    schema: str,
    term_mapping: str,
) -> Tuple[str, float, dict]:
    """
    Generate SQL using the specified model configuration.

    Args:
        config: Evaluation config dict (provider, model, prompt_type, ...).
        question: Natural language question.
        schema: Database schema text.
        term_mapping: Term mapping text.

    Returns:
        (sql_string, latency_seconds, token_info_dict)
        token_info_dict has keys: input_tokens, output_tokens
    """
    provider = config["provider"]
    model = config["model"]
    prompt_type = config["prompt_type"]

    token_info: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

    # ------------------------------------------------------------------
    # Anthropic path
    # ------------------------------------------------------------------
    if provider == "anthropic":
        client = anthropic.Anthropic()

        if prompt_type == "full":
            user_prompt = get_sql_prompt(
                user_question=question,
                schema_info=schema,
                term_mapping=term_mapping,
                few_shot_examples="",
                conversation_context="",
            )
            messages = [{"role": "user", "content": user_prompt}]
            system_msg = SYSTEM_MESSAGE
        else:
            # finetuned prompt style (unlikely for Anthropic, but supported)
            lc_messages = get_finetuned_sql_prompt(
                user_question=question,
                schema_info=schema,
                term_mapping=term_mapping,
            )
            system_msg = lc_messages[0].content
            messages = [{"role": "user", "content": lc_messages[1].content}]

        start = time.time()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_msg,
            messages=messages,
        )
        latency = time.time() - start

        sql = response.content[0].text.strip()
        token_info["input_tokens"] = response.usage.input_tokens
        token_info["output_tokens"] = response.usage.output_tokens

    # ------------------------------------------------------------------
    # OpenAI path
    # ------------------------------------------------------------------
    elif provider == "openai":
        client = openai.OpenAI()

        if prompt_type == "full":
            user_prompt = get_sql_prompt(
                user_question=question,
                schema_info=schema,
                term_mapping=term_mapping,
                few_shot_examples="",
                conversation_context="",
            )
            messages = [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]
        elif prompt_type == "finetuned":
            lc_messages = get_finetuned_sql_prompt(
                user_question=question,
                schema_info=schema,
                term_mapping=term_mapping,
            )
            messages = [
                {"role": "system", "content": lc_messages[0].content},
                {"role": "user", "content": lc_messages[1].content},
            ]
        else:
            raise ValueError(f"Unknown prompt_type: {prompt_type}")

        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0,
        )
        latency = time.time() - start

        sql = response.choices[0].message.content.strip()
        usage = response.usage
        token_info["input_tokens"] = usage.prompt_tokens
        token_info["output_tokens"] = usage.completion_tokens

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Strip markdown fences that models sometimes emit
    sql = _strip_sql_fences(sql)

    return sql, latency, token_info


def _strip_sql_fences(sql: str) -> str:
    """Remove optional ```sql ... ``` fences from model output."""
    text = sql.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```sql or ```)
        lines = lines[1:]
        # Remove last line if it is ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


# ---------------------------------------------------------------------------
# Single test-case evaluation
# ---------------------------------------------------------------------------

async def evaluate_single(
    test_case: dict,
    config: dict,
    pool: asyncpg.Pool,
) -> dict:
    """
    Evaluate a single test case against a model configuration.

    Args:
        test_case: Dict with at least 'question'; optionally 'expected_sql',
                   'expected_result', 'schema_tables', 'market'.
        config: Model configuration dict.
        pool: asyncpg connection pool.

    Returns:
        Dict with evaluation metrics for this test case.
    """
    question = test_case.get("question", "")
    expected_sql = test_case.get("expected_sql", "")

    # Build schema text -- use full schema for simplicity in evaluation
    schema_text = _build_full_prompt_schema()
    term_mapping = TERM_MAPPING_TEXT

    result: Dict[str, Any] = {
        "question": question,
        "config_name": config["name"],
        "model": config["model"],
    }

    # Generate SQL
    try:
        sql, latency, token_info = await asyncio.to_thread(
            lambda: asyncio.get_event_loop().run_until_complete(
                _generate_wrapper(config, question, schema_text, term_mapping)
            )
        )
    except Exception:
        # Fall back to synchronous generation in the current loop
        try:
            sql, latency, token_info = await _generate_wrapper(
                config, question, schema_text, term_mapping
            )
        except Exception as exc:
            result.update({
                "generated_sql": "",
                "sql_valid": False,
                "latency_seconds": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "result_match": False,
                "error": str(exc),
            })
            return result

    result["generated_sql"] = sql
    result["latency_seconds"] = round(latency, 4)
    result["input_tokens"] = token_info["input_tokens"]
    result["output_tokens"] = token_info["output_tokens"]
    result["cost_usd"] = round(
        _estimate_cost(config["model"], token_info["input_tokens"], token_info["output_tokens"]),
        6,
    )

    # Validate SQL via EXPLAIN
    result["sql_valid"] = await validate_sql(sql, pool)

    # Result accuracy: compare with expected SQL results if available
    result["result_match"] = False
    if expected_sql and result["sql_valid"]:
        expected_result = await execute_sql(expected_sql, pool)
        actual_result = await execute_sql(sql, pool)
        if expected_result is not None and actual_result is not None:
            result["result_match"] = _compare_results(expected_result, actual_result)

    return result


async def _generate_wrapper(
    config: dict,
    question: str,
    schema_text: str,
    term_mapping: str,
) -> Tuple[str, float, dict]:
    """Thin async wrapper around generate_sql_with_config (which uses sync clients)."""
    # anthropic.Anthropic() and openai.OpenAI() are synchronous clients,
    # so we run them directly. The 'async' is for interface consistency.
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _sync_generate,
        config,
        question,
        schema_text,
        term_mapping,
    )


def _sync_generate(
    config: dict,
    question: str,
    schema_text: str,
    term_mapping: str,
) -> Tuple[str, float, dict]:
    """Synchronous SQL generation call (runs in thread pool)."""
    provider = config["provider"]
    model = config["model"]
    prompt_type = config["prompt_type"]

    token_info: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

    if provider == "anthropic":
        client = anthropic.Anthropic()
        if prompt_type == "full":
            user_prompt = get_sql_prompt(
                user_question=question,
                schema_info=schema_text,
                term_mapping=term_mapping,
                few_shot_examples="",
                conversation_context="",
            )
            messages = [{"role": "user", "content": user_prompt}]
            system_msg = SYSTEM_MESSAGE
        else:
            lc_messages = get_finetuned_sql_prompt(
                user_question=question,
                schema_info=schema_text,
                term_mapping=term_mapping,
            )
            system_msg = lc_messages[0].content
            messages = [{"role": "user", "content": lc_messages[1].content}]

        start = time.time()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_msg,
            messages=messages,
        )
        latency = time.time() - start
        sql = response.content[0].text.strip()
        token_info["input_tokens"] = response.usage.input_tokens
        token_info["output_tokens"] = response.usage.output_tokens

    elif provider == "openai":
        client = openai.OpenAI()
        if prompt_type == "full":
            user_prompt = get_sql_prompt(
                user_question=question,
                schema_info=schema_text,
                term_mapping=term_mapping,
                few_shot_examples="",
                conversation_context="",
            )
            messages = [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_prompt},
            ]
        elif prompt_type == "finetuned":
            lc_messages = get_finetuned_sql_prompt(
                user_question=question,
                schema_info=schema_text,
                term_mapping=term_mapping,
            )
            messages = [
                {"role": "system", "content": lc_messages[0].content},
                {"role": "user", "content": lc_messages[1].content},
            ]
        else:
            raise ValueError(f"Unknown prompt_type: {prompt_type}")

        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024,
            temperature=0,
        )
        latency = time.time() - start
        sql = response.choices[0].message.content.strip()
        usage = response.usage
        token_info["input_tokens"] = usage.prompt_tokens
        token_info["output_tokens"] = usage.completion_tokens

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    sql = _strip_sql_fences(sql)
    return sql, latency, token_info


def _compare_results(expected: List[dict], actual: List[dict]) -> bool:
    """
    Compare two query result sets for equivalence.

    Converts all values to strings for a deterministic comparison,
    and sorts rows to handle order differences.
    """
    def normalize(rows: List[dict]) -> List[tuple]:
        if not rows:
            return []
        keys = sorted(rows[0].keys())
        return sorted(tuple(str(row.get(k, "")) for k in keys) for row in rows)

    return normalize(expected) == normalize(actual)


# ---------------------------------------------------------------------------
# Full evaluation run
# ---------------------------------------------------------------------------

async def run_evaluation(
    test_cases: List[dict],
    configs: List[dict],
    pool: asyncpg.Pool,
) -> dict:
    """
    Run evaluation across all test cases and configs.

    Args:
        test_cases: List of test case dicts.
        configs: List of model configuration dicts.
        pool: asyncpg connection pool.

    Returns:
        Dict keyed by config name with aggregated metrics and per-case details.
    """
    results: Dict[str, Any] = {}

    for config in configs:
        name = config["name"]
        if config["model"] is None:
            print(f"[SKIP] {name}: model is not set (None). "
                  "Pass --finetuned-model to specify.")
            results[name] = {
                "config": config,
                "skipped": True,
                "reason": "model not set",
            }
            continue

        print(f"\n{'='*60}")
        print(f"Evaluating: {name} ({config['description']})")
        print(f"{'='*60}")

        case_results: List[dict] = []
        for idx, tc in enumerate(test_cases, 1):
            print(f"  [{idx}/{len(test_cases)}] {tc.get('question', '')[:60]}...", end=" ")
            case_result = await evaluate_single(tc, config, pool)
            case_results.append(case_result)
            status = "VALID" if case_result.get("sql_valid") else "INVALID"
            print(f"{status} ({case_result.get('latency_seconds', 0):.2f}s)")

        # Aggregate metrics
        total = len(case_results)
        valid_count = sum(1 for r in case_results if r.get("sql_valid"))
        match_count = sum(1 for r in case_results if r.get("result_match"))
        latencies = [r["latency_seconds"] for r in case_results if "latency_seconds" in r]
        input_tokens = [r["input_tokens"] for r in case_results if "input_tokens" in r]
        output_tokens = [r["output_tokens"] for r in case_results if "output_tokens" in r]
        costs = [r["cost_usd"] for r in case_results if "cost_usd" in r]

        results[name] = {
            "config": config,
            "skipped": False,
            "total_cases": total,
            "sql_validity_rate": round(valid_count / total * 100, 1) if total else 0.0,
            "result_match_rate": round(match_count / total * 100, 1) if total else 0.0,
            "avg_latency": round(sum(latencies) / len(latencies), 3) if latencies else 0.0,
            "avg_input_tokens": round(sum(input_tokens) / len(input_tokens), 0) if input_tokens else 0,
            "avg_output_tokens": round(sum(output_tokens) / len(output_tokens), 0) if output_tokens else 0,
            "avg_cost_usd": round(sum(costs) / len(costs), 6) if costs else 0.0,
            "total_cost_usd": round(sum(costs), 4) if costs else 0.0,
            "details": case_results,
        }

    return results


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def print_comparison_table(results: dict) -> None:
    """Print a formatted comparison table of evaluation results."""
    # Collect non-skipped config names
    active = [name for name, data in results.items() if not data.get("skipped")]
    if not active:
        print("\nNo configurations were evaluated.")
        return

    # Determine column widths
    label_width = 22
    col_width = max(16, max(len(n) for n in active) + 2)

    # Header
    header = f"| {'Metric':<{label_width}} |"
    separator = f"|{'-' * (label_width + 2)}|"
    for name in active:
        header += f" {name:^{col_width}} |"
        separator += f"{'-' * (col_width + 2)}|"

    print(f"\n{separator}")
    print(header)
    print(separator)

    # Rows
    metrics = [
        ("SQL Validity (%)", "sql_validity_rate", "{:.1f}"),
        ("Result Match (%)", "result_match_rate", "{:.1f}"),
        ("Avg Latency (s)", "avg_latency", "{:.3f}"),
        ("Avg Input Tokens", "avg_input_tokens", "{:.0f}"),
        ("Avg Output Tokens", "avg_output_tokens", "{:.0f}"),
        ("Est. Cost/Query ($)", "avg_cost_usd", "{:.6f}"),
        ("Total Cost ($)", "total_cost_usd", "{:.4f}"),
        ("Total Cases", "total_cases", "{:d}"),
    ]

    for label, key, fmt in metrics:
        row = f"| {label:<{label_width}} |"
        for name in active:
            value = results[name].get(key, 0)
            if isinstance(value, float):
                formatted = fmt.format(value)
            else:
                formatted = fmt.format(int(value))
            row += f" {formatted:^{col_width}} |"
        print(row)

    print(separator)

    # Skipped configs
    skipped = [name for name, data in results.items() if data.get("skipped")]
    if skipped:
        print(f"\nSkipped: {', '.join(skipped)}")


# ---------------------------------------------------------------------------
# Deployment criteria check
# ---------------------------------------------------------------------------

def check_deployment_criteria(results: dict) -> bool:
    """
    Check whether the fine-tuned model (config B) meets deployment thresholds.

    Compares B's metrics against DEPLOYMENT_THRESHOLDS and also checks for
    regressions on complex queries relative to config A.

    Returns True if all criteria pass, False otherwise.
    """
    b_key = "B_finetuned"
    a_key = "A_claude_current"

    if b_key not in results or results[b_key].get("skipped"):
        print("\n[DEPLOY CHECK] Fine-tuned model (B) was not evaluated -- cannot assess.")
        return False

    b = results[b_key]
    passed = True

    print("\n" + "=" * 60)
    print("Deployment Criteria Check")
    print("=" * 60)

    # 1. SQL validity rate
    threshold_validity = DEPLOYMENT_THRESHOLDS.get("sql_validity_rate", 0.90) * 100
    actual_validity = b.get("sql_validity_rate", 0.0)
    ok = actual_validity >= threshold_validity
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] SQL Validity: {actual_validity:.1f}% (threshold >= {threshold_validity:.0f}%)")
    if not ok:
        passed = False

    # 2. Average latency
    threshold_latency = DEPLOYMENT_THRESHOLDS.get("max_latency_seconds", 2.0)
    actual_latency = b.get("avg_latency", 0.0)
    ok = actual_latency < threshold_latency
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] Avg Latency: {actual_latency:.3f}s (threshold < {threshold_latency:.1f}s)")
    if not ok:
        passed = False

    # 3. Complex query regression (compare B vs A on validity)
    max_regression = DEPLOYMENT_THRESHOLDS.get("complex_query_regression", 0)
    if a_key in results and not results[a_key].get("skipped"):
        a_validity = results[a_key].get("sql_validity_rate", 0.0)
        regression = a_validity - actual_validity
        ok = regression <= max_regression
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] Regression vs A: {regression:.1f}pp "
              f"(threshold <= {max_regression}pp)")
        if not ok:
            passed = False
    else:
        print("  [SKIP] Regression check: config A not available")

    # Overall
    overall = "PASS" if passed else "FAIL"
    print(f"\n  Overall: {overall}")
    print("=" * 60)

    return passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _load_test_cases(path: Path) -> List[dict]:
    """Load test cases from a JSONL file (one JSON object per line)."""
    cases: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            # Support OpenAI fine-tuning format: extract user question
            if "messages" in obj:
                question = ""
                expected_sql = ""
                for msg in obj["messages"]:
                    if msg["role"] == "user":
                        question = msg["content"]
                    elif msg["role"] == "assistant":
                        expected_sql = msg["content"]
                cases.append({
                    "question": question,
                    "expected_sql": expected_sql,
                })
            else:
                cases.append(obj)
    return cases


def _save_results(results: dict, path: Path) -> None:
    """Save evaluation results to a JSON file."""
    # Convert non-serializable values
    serializable = {}
    for name, data in results.items():
        entry = {}
        for k, v in data.items():
            if k == "config":
                entry[k] = v
            elif k == "details":
                # Sanitize individual detail rows
                sanitized = []
                for row in v:
                    sanitized_row = {}
                    for rk, rv in row.items():
                        if isinstance(rv, (str, int, float, bool, type(None))):
                            sanitized_row[rk] = rv
                        else:
                            sanitized_row[rk] = str(rv)
                    sanitized.append(sanitized_row)
                entry[k] = sanitized
            else:
                entry[k] = v
        serializable[name] = entry

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to {path}")


async def main() -> None:
    """Entry point: parse arguments, run evaluation, report results."""
    parser = argparse.ArgumentParser(
        description="Evaluate and compare SQL generation across model configurations."
    )
    parser.add_argument(
        "--test-data",
        type=str,
        default=str(TEST_SET_PATH),
        help="Path to test set JSONL file.",
    )
    parser.add_argument(
        "--finetuned-model",
        type=str,
        default=None,
        help="Fine-tuned model ID (e.g., ft:<base>:<org>:<suffix>:<id>). "
             "Overrides EVAL_CONFIGS[1].model.",
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=DATABASE_URL,
        help="PostgreSQL connection string.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(EVALUATION_RESULTS_PATH),
        help="Path for evaluation results JSON output.",
    )
    args = parser.parse_args()

    # Load test data
    test_data_path = Path(args.test_data)
    if not test_data_path.exists():
        print(f"Error: test data file not found at {test_data_path}")
        sys.exit(1)

    test_cases = _load_test_cases(test_data_path)
    print(f"Loaded {len(test_cases)} test cases from {test_data_path}")

    # Prepare configs (deep copy to avoid mutating the originals)
    configs = deepcopy(EVAL_CONFIGS)
    if args.finetuned_model:
        configs[1]["model"] = args.finetuned_model
        print(f"Fine-tuned model set to: {args.finetuned_model}")

    # Validate database URL
    db_url = args.database_url
    if not db_url:
        print("Error: DATABASE_URL is not set. Provide via --database-url or env var.")
        sys.exit(1)

    # Connect to database
    print(f"Connecting to database...")
    try:
        pool = await asyncpg.create_pool(db_url, min_size=2, max_size=5)
    except Exception as exc:
        print(f"Error: failed to connect to database: {exc}")
        sys.exit(1)

    try:
        # Run evaluation
        results = await run_evaluation(test_cases, configs, pool)

        # Print comparison table
        print_comparison_table(results)

        # Check deployment criteria for fine-tuned model
        check_deployment_criteria(results)

        # Save detailed results
        output_path = Path(args.output)
        _save_results(results, output_path)

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
