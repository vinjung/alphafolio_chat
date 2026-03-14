#api/app/core/llm/types.py
from enum import Enum


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google_genai"
    PERPLEXITY = "perplexity"  # Perplexity 추가
    GROK = "grok"
