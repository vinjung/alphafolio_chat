# fine_tuning/config.py
"""
Fine-tuning Configuration

Central configuration for training data preparation, model training,
and evaluation parameters.
"""
import os
from pathlib import Path


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Output files
TRAINING_DATA_PATH = DATA_DIR / "training_data.jsonl"
VALIDATION_DATA_PATH = DATA_DIR / "validation_data.jsonl"
TEST_SET_PATH = DATA_DIR / "test_set.jsonl"
SYNTHETIC_DATA_PATH = DATA_DIR / "synthetic_data.jsonl"
EVALUATION_RESULTS_PATH = DATA_DIR / "evaluation_results.json"


# =============================================================================
# SYSTEM MESSAGE (shared across training and inference)
# =============================================================================

SYSTEM_MESSAGE = (
    "You are a PostgreSQL expert for Korean and US financial stock data analysis. "
    "Generate accurate, executable SQL based on the provided schema and question. "
    "Output only the SQL query without markdown or explanation."
)


# =============================================================================
# DATA SPLIT RATIOS
# =============================================================================

TRAIN_RATIO = 0.80
VALIDATION_RATIO = 0.10
TEST_RATIO = 0.10


# =============================================================================
# FINE-TUNING HYPERPARAMETERS
# =============================================================================

BASE_MODEL = "gpt-4.1-mini-2025-04-14"
MODEL_SUFFIX = "sql-ft"
N_EPOCHS = 3
# batch_size and learning_rate_multiplier are set to "auto" by default


# =============================================================================
# SYNTHETIC DATA GENERATION
# =============================================================================

# Target total examples (including original 156)
TARGET_TOTAL_EXAMPLES = 700

# Generation strategies and approximate targets
PARAPHRASE_TARGET = 250
PARAMETER_VARIATION_TARGET = 150
NOVEL_COMPLEX_TARGET = 100

# Claude model for synthetic generation
SYNTHETIC_GENERATION_MODEL = "claude-sonnet-4-20250514"
SYNTHETIC_GENERATION_PROVIDER = "anthropic"

# Batch size for generation requests
GENERATION_BATCH_SIZE = 10


# =============================================================================
# EVALUATION
# =============================================================================

# Models to compare
EVAL_CONFIGS = [
    {
        "name": "A_claude_current",
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "prompt_type": "full",
        "description": "Current production: Claude Sonnet 4 + full prompt"
    },
    {
        "name": "B_finetuned",
        "provider": "openai",
        "model": None,  # Set to fine-tuned model ID after training
        "prompt_type": "finetuned",
        "description": "Fine-tuned: gpt-4.1-mini + simplified prompt"
    },
    {
        "name": "C_base_gpt4o_mini",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "prompt_type": "full",
        "description": "Control: base gpt-4o-mini + full prompt"
    },
    {
        "name": "D_gpt41_nano",
        "provider": "openai",
        "model": "gpt-4.1-nano",
        "prompt_type": "full",
        "description": "Base gpt-4.1-nano + full prompt"
    },
    {
        "name": "E_gpt41_mini",
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "prompt_type": "full",
        "description": "Base gpt-4.1-mini + full prompt"
    },
    {
        "name": "F_gpt41",
        "provider": "openai",
        "model": "gpt-4.1",
        "prompt_type": "full",
        "description": "Base gpt-4.1 + full prompt"
    },
]

# Evaluation thresholds for deployment
DEPLOYMENT_THRESHOLDS = {
    "sql_validity_rate": 0.90,      # >= 90% EXPLAIN pass rate
    "max_latency_seconds": 2.0,     # < 2 seconds average
    "complex_query_regression": 0,  # No regression on CTE/multi-JOIN queries
}


# =============================================================================
# DATABASE
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "")
