# fine_tuning/prepare_training_data.py
"""
Training Data Preparation for OpenAI Fine-Tuning

Converts 156 few-shot examples into OpenAI fine-tuning JSONL format.
Each example includes only the relevant schema (tables used in the SQL),
term mapping, and the clean SQL output.

Usage:
    python -m fine_tuning.prepare_training_data
    python -m fine_tuning.prepare_training_data --output data/custom_output.jsonl
"""
import sys
import os
import re
import json
import argparse
from pathlib import Path
from collections import Counter
from typing import List, Dict, Set

# Add project root to sys.path so imports work when running the script directly
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.chat.alpha_ai_model.prompts.few_shot_examples import FEW_SHOT_EXAMPLES
from services.chat.alpha_ai_model.prompts.sql_prompt import ALL_SCHEMAS, TERM_MAPPING_TEXT
from fine_tuning.config import SYSTEM_MESSAGE, DATA_DIR, TRAINING_DATA_PATH


def extract_tables_from_sql(sql: str, known_tables: List[str]) -> List[str]:
    """
    Extract table names referenced in a SQL query by matching against known table names.

    Uses word-boundary regex to find table names that appear in the SQL.
    Sorts results to ensure deterministic ordering.

    Args:
        sql: The SQL query string to parse
        known_tables: List of known table names from ALL_SCHEMAS

    Returns:
        Sorted list of matched table names found in the SQL
    """
    matched_tables: Set[str] = set()
    sql_lower = sql.lower()

    for table_name in known_tables:
        pattern = r'\b' + re.escape(table_name) + r'\b'
        if re.search(pattern, sql_lower):
            matched_tables.add(table_name)

    return sorted(matched_tables)


def clean_sql(sql: str) -> str:
    """
    Clean SQL string by removing markdown formatting and trailing semicolons.

    Strips:
        - Markdown code fences (```sql ... ```)
        - Leading/trailing whitespace
        - Trailing semicolons

    Args:
        sql: Raw SQL string potentially containing markdown

    Returns:
        Clean SQL string ready for fine-tuning output
    """
    cleaned = sql.strip()

    # Remove markdown code fences
    cleaned = re.sub(r'^```(?:sql)?\s*', '', cleaned)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned)

    # Strip again after removing fences
    cleaned = cleaned.strip()

    # Remove trailing semicolons
    cleaned = cleaned.rstrip(';').strip()

    return cleaned


def get_relevant_schema(table_names: List[str]) -> str:
    """
    Build a schema string containing only the tables referenced in the SQL.

    Args:
        table_names: List of table names to include

    Returns:
        Concatenated schema text for the relevant tables
    """
    schema_parts = []
    for table_name in table_names:
        if table_name in ALL_SCHEMAS:
            schema_parts.append(ALL_SCHEMAS[table_name].strip())

    return "\n\n".join(schema_parts)


def format_training_example(example: Dict[str, str]) -> Dict:
    """
    Convert a single few-shot example into OpenAI fine-tuning message format.

    The format follows OpenAI's chat completion fine-tuning structure:
    - system: Short system message defining the role
    - user: Relevant schema + term mapping + question
    - assistant: Clean SQL query

    Args:
        example: Dictionary with 'question', 'sql', 'category', 'market' keys

    Returns:
        Dictionary in OpenAI fine-tuning JSONL format with 'messages' key
    """
    question = example["question"]
    raw_sql = example["sql"]

    # Extract tables used in this SQL
    known_tables = list(ALL_SCHEMAS.keys())
    tables_used = extract_tables_from_sql(raw_sql, known_tables)

    # Build relevant schema (only tables used in the query)
    relevant_schema = get_relevant_schema(tables_used)

    # If no tables matched (unlikely), fall back to empty schema note
    if not relevant_schema:
        relevant_schema = "(No specific table schema matched)"

    # Build user message content
    user_content = (
        f"## Database Schema\n{relevant_schema}\n\n"
        f"## Term Mapping\n{TERM_MAPPING_TEXT.strip()}\n\n"
        f"## Question\n{question}"
    )

    # Clean the SQL for assistant output
    assistant_content = clean_sql(raw_sql)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def print_statistics(examples: List[Dict[str, str]]) -> None:
    """
    Print summary statistics about the processed examples.

    Args:
        examples: The list of few-shot example dictionaries
    """
    total = len(examples)
    category_counts = Counter(ex.get("category", "unknown") for ex in examples)
    market_counts = Counter(ex.get("market", "unknown") for ex in examples)

    print(f"\n{'='*60}")
    print(f"Training Data Preparation Complete")
    print(f"{'='*60}")
    print(f"\nTotal examples: {total}")

    print(f"\n--- Examples per Category ---")
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {category:<30s} {count:>4d}")

    print(f"\n--- Examples per Market ---")
    for market, count in sorted(market_counts.items(), key=lambda x: -x[1]):
        print(f"  {market:<30s} {count:>4d}")

    print(f"\n{'='*60}")


def main() -> None:
    """
    Main entry point for training data preparation.

    Processes all few-shot examples, converts them to OpenAI fine-tuning
    JSONL format, and writes the output file. Prints statistics on completion.
    """
    parser = argparse.ArgumentParser(
        description="Convert few-shot examples to OpenAI fine-tuning JSONL format"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSONL file path (default: data/all_examples.jsonl)"
    )
    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
        # If relative path, resolve relative to DATA_DIR
        if not output_path.is_absolute():
            output_path = DATA_DIR / output_path
    else:
        output_path = DATA_DIR / "all_examples.jsonl"

    # Create DATA_DIR if it does not exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Processing {len(FEW_SHOT_EXAMPLES)} few-shot examples...")
    print(f"Output path: {output_path}")

    # Process all examples
    training_records = []
    skipped = 0

    for i, example in enumerate(FEW_SHOT_EXAMPLES):
        question = example.get("question", "")
        sql = example.get("sql", "")

        if not question or not sql:
            print(f"  [WARNING] Skipping example {i}: missing question or sql")
            skipped += 1
            continue

        record = format_training_example(example)
        training_records.append(record)

    # Write JSONL output
    with open(output_path, "w", encoding="utf-8") as f:
        for record in training_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(training_records)} training examples to {output_path}")
    if skipped > 0:
        print(f"Skipped {skipped} examples (missing question or sql)")

    # Print statistics
    print_statistics(FEW_SHOT_EXAMPLES)


if __name__ == "__main__":
    main()
