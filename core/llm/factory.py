from typing import Optional
from core.llm.types import LLMProvider
from config import settings
import os


def _get_default_model(provider: LLMProvider) -> str:
    """각 provider의 기본 모델명 반환"""
    model_defaults = {
        LLMProvider.OPENAI: 'gpt-4o',
        LLMProvider.ANTHROPIC: 'claude-sonnet-4-6',
        LLMProvider.PERPLEXITY: 'llama-3.1-sonar-large-128k-online',
        LLMProvider.GROK: 'grok-4'
    }

    if provider == LLMProvider.GOOGLE:
        raise NotImplementedError("Google provider not implemented")

    return model_defaults.get(provider, 'gpt-4o')


def _create_anthropic_client(model_name: str, **kwargs):
    """Anthropic 클라이언트 생성"""
    if settings.anthropic_api_key:
        os.environ['ANTHROPIC_API_KEY'] = settings.anthropic_api_key
    from langchain_anthropic import ChatAnthropic

    # 기본값 설정
    default_kwargs = {
        'timeout': kwargs.pop('timeout', 120),  # 2분 타임아웃
        'max_retries': kwargs.pop('max_retries', 2),
        'streaming': kwargs.pop('streaming', True),
    }

    # ✅ 핵심 수정: max_tokens 기본값 설정 (응답 잘림 해결)
    # max_tokens가 명시적으로 전달된 경우 사용, 아니면 기본값 4000 적용
    if 'max_tokens' in kwargs:
        default_kwargs['max_tokens'] = kwargs.pop('max_tokens')
    else:
        # Claude Sonnet 4 최적 기본값: 4000 토큰
        default_kwargs['max_tokens'] = 4000

    return ChatAnthropic(model_name=model_name, **default_kwargs, **kwargs)


def _create_openai_client(model_name: str, **kwargs):
    """OpenAI 클라이언트 생성"""
    if settings.openai_api_key:
        os.environ['OPENAI_API_KEY'] = settings.openai_api_key
    from langchain_openai import ChatOpenAI

    # 기본값 설정
    default_kwargs = {
        'timeout': kwargs.pop('timeout', 120),  # 2분 타임아웃
        'max_retries': kwargs.pop('max_retries', 2),
        'streaming': kwargs.pop('streaming', True),
    }

    # max_tokens가 명시적으로 전달된 경우만 설정
    if 'max_tokens' in kwargs:
        default_kwargs['max_tokens'] = kwargs.pop('max_tokens')

    return ChatOpenAI(model=model_name, **default_kwargs, **kwargs)


def _create_google_client(model_name: str, **kwargs):
    """Google 클라이언트 생성"""
    if settings.google_api_key:
        os.environ['GOOGLE_API_KEY'] = settings.google_api_key
    from langchain_google_genai import ChatGoogleGenerativeAI

    # 기본값 설정
    default_kwargs = {
        'timeout': kwargs.pop('timeout', 120),  # 2분 타임아웃
        'max_retries': kwargs.pop('max_retries', 2),
    }

    # max_output_tokens가 명시적으로 전달된 경우만 설정
    if 'max_output_tokens' in kwargs:
        default_kwargs['max_output_tokens'] = kwargs.pop('max_output_tokens')

    return ChatGoogleGenerativeAI(model=model_name, **default_kwargs, **kwargs)


def _create_perplexity_client(model_name: str, **kwargs):
    """Perplexity 클라이언트 생성"""
    if settings.pplx_api_key:
        os.environ['PPLX_API_KEY'] = settings.pplx_api_key
    from langchain_perplexity import ChatPerplexity

    # 기본값 설정
    default_kwargs = {
        'timeout': kwargs.pop('timeout', 120),  # 2분 타임아웃
        'max_retries': kwargs.pop('max_retries', 2),
        'streaming': kwargs.pop('streaming', True),
    }

    # max_tokens가 명시적으로 전달된 경우만 설정
    if 'max_tokens' in kwargs:
        default_kwargs['max_tokens'] = kwargs.pop('max_tokens')

    return ChatPerplexity(model=model_name, **default_kwargs, **kwargs)

def _create_grok_client(model_name: str, **kwargs):
    """Perplexity 클라이언트 생성"""
    if settings.xai_api_key:
        os.environ['xai_api_key'] = settings.xai_api_key
    from langchain_xai import ChatXAI

    # 기본값 설정
    default_kwargs = {
        'timeout': kwargs.pop('timeout', 120),  # 2분 타임아웃
        'max_retries': kwargs.pop('max_retries', 2),
        'streaming': kwargs.pop('streaming', True),
    }

    # max_tokens가 명시적으로 전달된 경우만 설정
    if 'max_tokens' in kwargs:
        default_kwargs['max_tokens'] = kwargs.pop('max_tokens')

    return ChatXAI(model=model_name, **default_kwargs, **kwargs)


def get_llm(provider: LLMProvider, model_name: Optional[str] = None, **kwargs):
    """provider 및 model_name, model_config 정보로 Langchain LLM instance 반환"""
    # computed_field를 명시적으로 호출
    available_llms: set[LLMProvider] = settings.available_llms # type: ignore
    if provider not in available_llms:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    if model_name is None:
        model_name = _get_default_model(provider)

    # 로깅 추가
    from config import logger
    logger.info(f"🤖 Creating LLM client: provider={provider.value}, model={model_name}")
    if 'max_tokens' in kwargs:
        logger.info(f"🤖 Max tokens: {kwargs['max_tokens']}")
    # ✅ 추가: 기본값 사용 시에도 로깅
    elif provider == LLMProvider.ANTHROPIC:
        logger.info(f"🤖 Max tokens: 4000 (default)")

    # Provider별 클라이언트 생성
    client_creators = {
        LLMProvider.ANTHROPIC: _create_anthropic_client,
        LLMProvider.OPENAI: _create_openai_client,
        LLMProvider.GOOGLE: _create_google_client,
        LLMProvider.PERPLEXITY: _create_perplexity_client,
        LLMProvider.GROK: _create_grok_client
    }

    creator = client_creators.get(provider)
    if creator:
        llm = creator(model_name, **kwargs)
    else:
        # fallback
        from langchain.chat_models import init_chat_model
        llm = init_chat_model(model=model_name, model_provider=provider.value, **kwargs)

    # Wrap with concurrency limiter
    from core.llm.concurrency_limiter import wrap_llm_with_concurrency_limit
    return wrap_llm_with_concurrency_limit(llm, provider)
