# services/chat/alpha_ai_model/prompts/sql_prompt_finetuned.py
"""
Fine-tuned Model SQL Generation Prompt

Simplified prompt template for fine-tuned SQL generation model.
Rules and patterns are internalized during training, so only dynamic
context (schema, term mapping, conversation) is included.
"""
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage


FINETUNED_SQL_SYSTEM_MESSAGE = (
    "You are a PostgreSQL expert for Korean and US financial stock data analysis. "
    "Generate accurate, executable SQL based on the provided schema and question. "
    "Output only the SQL query without markdown or explanation."
)

FINETUNED_SQL_USER_TEMPLATE = """## Database Schema
{schema_info}

## Term Mapping
{term_mapping}

## SQL Rules
1. NEVER use >= CURRENT_DATE or = CURRENT_DATE for data queries. Use MAX(date) subquery instead.
   - Price/indicator tables: WHERE date = (SELECT MAX(date) FROM table_name)
   - Dividend tables (us_dividends, kr_dividends): WHERE ex_dividend_date >= (SELECT MAX(ex_dividend_date) FROM table) - INTERVAL '3 months'
   - Earnings tables: WHERE report_date >= (SELECT MAX(report_date) FROM table) - INTERVAL '6 months'
2. For ranking queries (ORDER BY ... DESC/ASC LIMIT N) on tables with multiple rows per symbol:
   - Deduplicate by symbol using: DISTINCT ON (symbol) ... ORDER BY symbol, rank_column DESC
   - Or use ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) to keep latest per symbol

## Conversation Context
{conversation_context}

## Question
{user_question}"""


def get_finetuned_sql_prompt(
    user_question: str,
    schema_info: str,
    term_mapping: str,
    conversation_context: str = ""
) -> List:
    """
    Generate simplified prompt for fine-tuned SQL model.

    The fine-tuned model has internalized SQL generation rules, few-shot patterns,
    and table usage conventions during training. Only dynamic, query-specific
    context is provided.

    Args:
        user_question: User's natural language question
        schema_info: Relevant table/column schema (RAG-retrieved)
        term_mapping: Korean term to SQL column mappings (RAG-retrieved)
        conversation_context: Previous conversation for context resolution

    Returns:
        List of LangChain messages [SystemMessage, HumanMessage]
    """
    if not conversation_context:
        conversation_context = "(No previous conversation in this session)"

    user_content = FINETUNED_SQL_USER_TEMPLATE.format(
        schema_info=schema_info,
        term_mapping=term_mapping,
        conversation_context=conversation_context,
        user_question=user_question
    )

    return [
        SystemMessage(content=FINETUNED_SQL_SYSTEM_MESSAGE),
        HumanMessage(content=user_content)
    ]
