#!/usr/bin/env python3
# fine_tuning/reformat_synthetic_data.py
"""
Reformat Existing Synthetic Data to Schema Format (B-2)

Converts existing synthetic_data.jsonl (plain question format) into
the standardized schema format used during inference:
  ## Database Schema + ## Term Mapping + ## Question

This is a local-only transformation (no API calls).
Reuses extract_tables_from_sql() and get_relevant_schema() from
prepare_training_data.py for consistency.

Usage:
    python -m fine_tuning.reformat_synthetic_data
    python -m fine_tuning.reformat_synthetic_data --input data/synthetic_data.jsonl --output data/synthetic_data_formatted.jsonl
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from collections import Counter

# Add project root to sys.path so imports work when running the script directly
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fine_tuning.config import SYSTEM_MESSAGE, DATA_DIR, SYNTHETIC_DATA_PATH
from fine_tuning.prepare_training_data import (
    extract_tables_from_sql,
    get_relevant_schema,
    clean_sql,
)
from services.chat.alpha_ai_model.prompts.sql_prompt import ALL_SCHEMAS, TERM_MAPPING_TEXT

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def reformat_example(example: dict) -> dict:
    """
    Reformat a single synthetic training example from plain question format
    to the schema-enriched format.

    Input format (plain):
        messages: [system, user(plain question), assistant(sql)]

    Output format (schema):
        messages: [system, user(schema + term_mapping + question), assistant(sql)]

    Args:
        example: A training example dict with 'messages' key.

    Returns:
        Reformatted example dict, or None if reformatting fails.
    """
    messages = example.get("messages", [])
    if len(messages) < 3:
        return None

    # Extract user question and assistant SQL
    user_msg = messages[1]
    assistant_msg = messages[2]

    user_content = user_msg.get("content", "")
    sql_content = assistant_msg.get("content", "")

    if not user_content or not sql_content:
        return None

    # Check if already in schema format (skip reformatting)
    if user_content.strip().startswith("## Database Schema"):
        return example

    # Extract the question text (the entire user content is the question)
    question = user_content.strip()

    # Extract tables used in the SQL
    known_tables = list(ALL_SCHEMAS.keys())
    tables_used = extract_tables_from_sql(sql_content, known_tables)

    # Build relevant schema (only tables used in the query)
    relevant_schema = get_relevant_schema(tables_used)
    if not relevant_schema:
        relevant_schema = "(No specific table schema matched)"

    # Build new user content with schema format
    new_user_content = (
        f"## Database Schema\n{relevant_schema}\n\n"
        f"## Term Mapping\n{TERM_MAPPING_TEXT.strip()}\n\n"
        f"## Question\n{question}"
    )

    # Clean the SQL for assistant output
    cleaned_sql = clean_sql(sql_content)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": new_user_content},
            {"role": "assistant", "content": cleaned_sql},
        ]
    }


def main() -> None:
    """
    Main entry point for reformatting synthetic data.

    Reads existing synthetic_data.jsonl, reformats each example to include
    schema information, and writes to synthetic_data_formatted.jsonl.
    """
    parser = argparse.ArgumentParser(
        description="Reformat synthetic training data to schema format"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Input JSONL file path (default: data/synthetic_data.jsonl)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSONL file path (default: data/synthetic_data_formatted.jsonl)"
    )
    args = parser.parse_args()

    # Determine input path
    if args.input:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = DATA_DIR / input_path
    else:
        input_path = SYNTHETIC_DATA_PATH

    # Determine output path
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = DATA_DIR / output_path
    else:
        output_path = DATA_DIR / "synthetic_data_formatted.jsonl"

    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Reading synthetic data from: %s", input_path)

    # Read input
    examples = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                examples.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("Skipping line %d: JSON decode error: %s", line_num, e)

    logger.info("Loaded %d examples from input", len(examples))

    # Reformat each example
    reformatted = []
    already_formatted = 0
    skipped = 0

    for i, example in enumerate(examples):
        result = reformat_example(example)
        if result is None:
            logger.warning("Skipping example %d: failed to reformat", i)
            skipped += 1
            continue

        # Check if it was already in schema format
        user_content = example.get("messages", [{}])[1].get("content", "") if len(example.get("messages", [])) > 1 else ""
        if user_content.strip().startswith("## Database Schema"):
            already_formatted += 1

        reformatted.append(result)

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        for record in reformatted:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # Print statistics
    print(f"\n{'='*60}")
    print(f"Synthetic Data Reformatting Complete")
    print(f"{'='*60}")
    print(f"\nInput file:  {input_path}")
    print(f"Output file: {output_path}")
    print(f"\nTotal input examples:     {len(examples)}")
    print(f"Already in schema format: {already_formatted}")
    print(f"Newly reformatted:        {len(reformatted) - already_formatted}")
    print(f"Skipped (errors):         {skipped}")
    print(f"Total output examples:    {len(reformatted)}")
    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
