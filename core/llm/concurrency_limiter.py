# core/llm/concurrency_limiter.py
"""
Per-provider LLM concurrency limiter.

Prevents overwhelming LLM API rate limits by limiting the number
of concurrent API calls per provider across all requests in a worker.

Each uvicorn worker has its own independent limiter instance.
"""
import asyncio
import functools
from typing import Dict
from core.llm.types import LLMProvider
from config import settings
import logging

logger = logging.getLogger(__name__)


class LLMConcurrencyLimiter:
    """
    Per-provider semaphore to limit concurrent LLM API calls.

    Defaults:
        - Anthropic: 5 concurrent calls (tier-based limit)
        - OpenAI: 10 concurrent calls (higher tier limits)
        - Others: 5 concurrent calls
    """

    def __init__(self):
        self._limiters: Dict[LLMProvider, asyncio.Semaphore] = {}
        self._defaults = {
            LLMProvider.ANTHROPIC: settings.LLM_MAX_CONCURRENT_ANTHROPIC,
            LLMProvider.OPENAI: settings.LLM_MAX_CONCURRENT_OPENAI,
        }
        logger.info(
            f"[LLMConcurrencyLimiter] Initialized: "
            f"Anthropic={self._defaults.get(LLMProvider.ANTHROPIC, 5)}, "
            f"OpenAI={self._defaults.get(LLMProvider.OPENAI, 10)}"
        )

    def get_limiter(self, provider: LLMProvider) -> asyncio.Semaphore:
        """Get or create a semaphore for the given provider."""
        if provider not in self._limiters:
            limit = self._defaults.get(provider, 5)
            self._limiters[provider] = asyncio.Semaphore(limit)
        return self._limiters[provider]


def wrap_llm_with_concurrency_limit(llm, provider: LLMProvider):
    """
    Wrap an LLM instance's ainvoke method with concurrency limiting.

    This monkey-patches the ainvoke method to acquire a per-provider
    semaphore before making the API call. The LLM instance remains
    a proper LangChain BaseChatModel, preserving LangGraph compatibility
    (isinstance checks, astream_events, etc.).

    Args:
        llm: LangChain BaseChatModel instance
        provider: LLM provider for semaphore selection

    Returns:
        The same LLM instance with wrapped ainvoke method
    """
    semaphore = llm_limiter.get_limiter(provider)
    original_ainvoke = llm.ainvoke

    @functools.wraps(original_ainvoke)
    async def limited_ainvoke(*args, **kwargs):
        async with semaphore:
            return await original_ainvoke(*args, **kwargs)

    llm.ainvoke = limited_ainvoke
    return llm


# Module-level singleton
llm_limiter = LLMConcurrencyLimiter()
