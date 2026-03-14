# services/chat/alpha_ai_model/prompts/__init__.py
"""
Alpha AI Prompts

System prompts, SQL generation prompts, and few-shot examples.
"""
from .system_prompt import SYSTEM_PROMPT, get_system_prompt
from .sql_prompt import SQL_GENERATION_PROMPT, get_sql_prompt
from .sql_prompt_finetuned import get_finetuned_sql_prompt
from .few_shot_examples import FEW_SHOT_EXAMPLES, get_few_shot_examples

__all__ = [
    "SYSTEM_PROMPT",
    "get_system_prompt",
    "SQL_GENERATION_PROMPT",
    "get_sql_prompt",
    "get_finetuned_sql_prompt",
    "FEW_SHOT_EXAMPLES",
    "get_few_shot_examples"
]
