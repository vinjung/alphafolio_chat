# fine_tuning/split_data.py
"""
Split Combined Training Data into Train / Validation / Test Sets

Reads one or more JSONL files, shuffles them with a fixed seed for
reproducibility, and writes three output splits (80/10/10 by default).

The split is stratified when possible: examples are grouped by an
inferred category derived from the user message content, and each
group is split independently so that category proportions are
roughly preserved across all three sets.

Usage:
    python -m fine_tuning.split_data --input data/all_examples.jsonl data/synthetic_data.jsonl
    python -m fine_tuning.split_data --input data/all_examples.jsonl --seed 123
"""
from __future__ import annotations

import sys
import os

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that `fine_tuning.config` can be
# imported regardless of how the script is invoked.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from fine_tuning.config import (
    DATA_DIR,
    TRAINING_DATA_PATH,
    VALIDATION_DATA_PATH,
    TEST_SET_PATH,
    TRAIN_RATIO,
    VALIDATION_RATIO,
    TEST_RATIO,
)


# =============================================================================
# Category inference
# =============================================================================

# Keyword patterns mapped to high-level query categories.
# Order matters: the first matching pattern wins.
_CATEGORY_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("aggregation",  re.compile(r"\b(sum|avg|average|count|total|mean|median|max|min)\b", re.IGNORECASE)),
    ("ranking",      re.compile(r"\b(rank|top|bottom|highest|lowest|best|worst|leader|laggard)\b", re.IGNORECASE)),
    ("time_series",  re.compile(r"\b(trend|daily|weekly|monthly|yearly|period|date|time.?series|quarter|yoy|mom|qoq)\b", re.IGNORECASE)),
    ("comparison",   re.compile(r"\b(compare|versus|vs|difference|gap|ratio|relative)\b", re.IGNORECASE)),
    ("filtering",    re.compile(r"\b(filter|where|condition|sector|industry|market.?cap|volume)\b", re.IGNORECASE)),
    ("join_complex", re.compile(r"\b(join|merge|combine|cte|subquery|nested|union|intersect)\b", re.IGNORECASE)),
]

_FALLBACK_CATEGORY = "general"


def _infer_category(example: dict) -> str:
    """Infer a rough category from the user message in an OpenAI chat-format example.

    The function looks at the ``messages`` list for a role=user entry and
    applies simple keyword matching.  Returns ``_FALLBACK_CATEGORY`` when
    nothing matches or the structure is unexpected.
    """
    messages = example.get("messages", [])
    user_text = ""
    for msg in messages:
        if msg.get("role") == "user":
            user_text = msg.get("content", "")
            break

    if not user_text:
        return _FALLBACK_CATEGORY

    for category, pattern in _CATEGORY_PATTERNS:
        if pattern.search(user_text):
            return category

    return _FALLBACK_CATEGORY


# =============================================================================
# I/O helpers
# =============================================================================

def load_jsonl(file_path: str) -> list:
    """Load a JSONL file and return a list of parsed JSON objects.

    Each line in the file must be a valid JSON object.  Blank lines are
    silently skipped.

    Parameters
    ----------
    file_path : str
        Path to the JSONL file.

    Returns
    -------
    list
        List of dictionaries parsed from the file.
    """
    data: list = []
    path = Path(file_path)
    if not path.exists():
        print(f"[WARNING] File not found, skipping: {file_path}")
        return data

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"[WARNING] Skipping invalid JSON at {file_path}:{line_no} - {exc}")
    return data


def save_jsonl(data: list, file_path: str) -> None:
    """Write a list of dictionaries to a JSONL file.

    Parameters
    ----------
    data : list
        List of JSON-serializable dictionaries.
    file_path : str
        Destination path.  Parent directories are created if necessary.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# =============================================================================
# Splitting logic
# =============================================================================

def split_data(
    data: list,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VALIDATION_RATIO,
    test_ratio: float = TEST_RATIO,
    seed: int = 42,
) -> Tuple[list, list, list]:
    """Split *data* into train / validation / test sets.

    The function first groups examples by an inferred category and splits
    each group independently so that the category distribution is roughly
    preserved across all three sets (stratified split).

    If a category group is too small to be split (fewer than 3 examples),
    all its examples are placed into the training set.

    Parameters
    ----------
    data : list
        Combined list of training examples (dicts).
    train_ratio : float
        Fraction allocated to the training set (default 0.80).
    val_ratio : float
        Fraction allocated to the validation set (default 0.10).
    test_ratio : float
        Fraction allocated to the test set (default 0.10).
    seed : int
        Random seed for reproducibility (default 42).

    Returns
    -------
    tuple[list, list, list]
        (train_data, val_data, test_data)
    """
    # Validate ratios
    ratio_sum = train_ratio + val_ratio + test_ratio
    if abs(ratio_sum - 1.0) > 1e-6:
        raise ValueError(
            f"Ratios must sum to 1.0, got {ratio_sum:.4f} "
            f"(train={train_ratio}, val={val_ratio}, test={test_ratio})"
        )

    rng = random.Random(seed)

    # Group by category for stratified splitting
    groups: Dict[str, list] = defaultdict(list)
    for example in data:
        cat = _infer_category(example)
        groups[cat].append(example)

    train_data: list = []
    val_data: list = []
    test_data: list = []

    for _category, items in sorted(groups.items()):
        rng.shuffle(items)
        n = len(items)

        if n < 3:
            # Too few to split meaningfully; put them all in training
            train_data.extend(items)
            continue

        n_train = max(1, round(n * train_ratio))
        n_val = max(1, round(n * val_ratio))
        # Ensure we don't exceed total count
        n_test = n - n_train - n_val
        if n_test < 0:
            # Adjust validation down if rounding pushed over
            n_val = n - n_train
            n_test = 0

        train_data.extend(items[:n_train])
        val_data.extend(items[n_train : n_train + n_val])
        test_data.extend(items[n_train + n_val :])

    # Final shuffle within each split so category blocks are not contiguous
    rng.shuffle(train_data)
    rng.shuffle(val_data)
    rng.shuffle(test_data)

    return train_data, val_data, test_data


# =============================================================================
# Statistics display
# =============================================================================

def _category_distribution(data: list) -> Dict[str, int]:
    """Return a mapping of category -> count for the given examples."""
    dist: Dict[str, int] = defaultdict(int)
    for example in data:
        dist[_infer_category(example)] += 1
    return dict(sorted(dist.items()))


def _print_distribution(label: str, data: list) -> None:
    """Print category distribution for a single split."""
    dist = _category_distribution(data)
    print(f"\n  [{label}] {len(data)} examples")
    for cat, cnt in dist.items():
        pct = cnt / len(data) * 100 if data else 0
        print(f"    {cat:<16s}: {cnt:>5d}  ({pct:5.1f}%)")


def print_statistics(
    total: int,
    train_data: list,
    val_data: list,
    test_data: list,
) -> None:
    """Print a summary of split sizes and category distributions."""
    print("=" * 60)
    print("DATA SPLIT STATISTICS")
    print("=" * 60)
    print(f"Total examples loaded : {total}")
    print(f"Training set          : {len(train_data)}  ({len(train_data)/total*100:.1f}%)" if total else "")
    print(f"Validation set        : {len(val_data)}  ({len(val_data)/total*100:.1f}%)" if total else "")
    print(f"Test set              : {len(test_data)}  ({len(test_data)/total*100:.1f}%)" if total else "")
    print("-" * 60)
    print("Category distribution per split:")

    _print_distribution("TRAIN", train_data)
    _print_distribution("VALID", val_data)
    _print_distribution("TEST", test_data)

    print("=" * 60)


# =============================================================================
# CLI entry point
# =============================================================================

def main() -> None:
    """Parse arguments, load data, split, save, and print statistics."""
    parser = argparse.ArgumentParser(
        description="Split combined JSONL training data into train / validation / test sets."
    )
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more input JSONL files (e.g., all_examples.jsonl synthetic_data.jsonl).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for shuffling (default: 42).",
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    all_data: list = []
    for fpath in args.input:
        loaded = load_jsonl(fpath)
        print(f"Loaded {len(loaded)} examples from {fpath}")
        all_data.extend(loaded)

    if not all_data:
        print("[ERROR] No examples loaded. Check input file paths.")
        sys.exit(1)

    total = len(all_data)
    print(f"\nTotal examples combined: {total}")

    # ------------------------------------------------------------------
    # Split
    # ------------------------------------------------------------------
    train_data, val_data, test_data = split_data(
        all_data,
        train_ratio=TRAIN_RATIO,
        val_ratio=VALIDATION_RATIO,
        test_ratio=TEST_RATIO,
        seed=args.seed,
    )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    save_jsonl(train_data, str(TRAINING_DATA_PATH))
    save_jsonl(val_data, str(VALIDATION_DATA_PATH))
    save_jsonl(test_data, str(TEST_SET_PATH))

    print(f"\nFiles written:")
    print(f"  Training   -> {TRAINING_DATA_PATH}")
    print(f"  Validation -> {VALIDATION_DATA_PATH}")
    print(f"  Test       -> {TEST_SET_PATH}")

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------
    print_statistics(total, train_data, val_data, test_data)


if __name__ == "__main__":
    main()
