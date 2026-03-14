# api/app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field, field_validator, model_validator
from typing import Optional, Any, Dict
from core.llm.types import LLMProvider
from db import create_pg_client, create_redis_clients, create_celery_client
import logging
import os


class Settings(BaseSettings):
    is_worker: Optional[bool] = Field(default=False, description="True if this is a worker.")

    # LLM ==============================================================================================================
    openai_api_key: Optional[str] = Field(default="", description="OpenAI API Key")
    anthropic_api_key: Optional[str] = Field(default="", description="Claude API Key")
    google_api_key: Optional[str] = Field(default="", description="Gemini API Key")
    pplx_api_key: Optional[str] = Field(default="", description="Perplexity API Key")
    xai_api_key: Optional[str] = Field(default="", description="XAI API Key")

    # DB ===============================================================================================================
    database_url: str = Field(default="", description="PostgreSQL Database URL")
    POSTGRES_POOL_MIN: Optional[int] = Field(default=1, description="PostgreSQL min pool")
    POSTGRES_POOL_MAX: Optional[int] = Field(default=15, description="PostgreSQL max pool")

    REDIS_URL: str = Field(default="", description="Redis URL")

    # ChromaDB =========================================================================================================
    CHROMA_HOST: Optional[str] = Field(default=None, description="ChromaDB server host (None for local file mode)")
    CHROMA_PORT: int = Field(default=8000, description="ChromaDB server port")

    # External APIs
    SERPER_API_KEY: Optional[str] = Field(default="", description="Serper API Key. 외부 웹 검색 엔진")
    KRX_API_KEY: Optional[str] = Field(default="", description="KRX API Key. 주식 데이터")
    FMP_API_KEY: Optional[str] = Field(default="", description="FMP 주식 데이터")
    MARKETSTACK_API_KEY: Optional[str] = Field(default="", description="Marketstack 주식 데이터")
    GOOGLE_CSE_ID: Optional[str] = Field(default="", description="Google Custom Search Engine ID")
    GOOGLE_CSE_API_KEY: Optional[str] = Field(default="", description="Google Custom Search API Key")
    DART_API_KEY: Optional[str] = Field(default="", description="DART API Key. 전자공시시스템")
    NAVER_CLIENT_ID: Optional[str] = Field(default="", description="Naver API Client ID")
    NAVER_CLIENT_SECRET: Optional[str] = Field(default="", description="Naver API Client Secret")

    # Redis ============================================================================================================
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL for Queue")

    # Fine-tuned Model ==================================================================================================
    fine_tuned_sql_model: Optional[str] = Field(
        default=None,
        description="Fine-tuned model ID for SQL generation (e.g., ft:<base_model>:<org>:<suffix>:<id>)"
    )
    fine_tuned_sql_enabled: bool = Field(
        default=False,
        description="Enable fine-tuned model for SQL generation instead of Claude"
    )
    fine_tuned_max_tables: int = Field(
        default=5,
        description="Maximum relevant tables for fine-tuned model. "
                    "Queries exceeding this route directly to Claude."
    )

    # Railway ==========================================================================================================
    railway_environment: str = Field(default="development", description="Railway Environment")

    # 🚀 Railway PORT 환경변수 자동 처리
    port: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "8000")),
        description="Server Port (Railway auto-assigns PORT env var)"
    )

    # CORS =============================================================================================================
    frontend_url: str = Field(default="http://localhost:3000", description="Frontend URL")

    # APP ==============================================================================================================
    logger_level: Optional[str] = Field(default="info", description="Logger Level")

    # Session Limits ===================================================================================================
    MAX_MESSAGES_PER_SESSION: int = Field(default=50, description="Maximum messages per session")
    MAX_TOKENS_PER_SESSION: int = Field(default=100_000, description="Maximum tokens per session (100K)")

    # Concurrency & Rate Limiting ======================================================================================
    MAX_CONCURRENT_REQUESTS: int = Field(default=5, description="Max concurrent requests in LangGraph pipeline per worker")
    MAX_WAITING_REQUESTS: int = Field(default=20, description="Max requests waiting in queue per worker")
    RATE_LIMIT_STREAM: str = Field(default="10/minute", description="Rate limit for SSE stream endpoint")
    RATE_LIMIT_CHAT: str = Field(default="30/minute", description="Rate limit for chat endpoint")

    # Multi-Worker =====================================================================================================
    UVICORN_WORKERS: int = Field(default=3, description="Number of uvicorn workers for production")

    # Unified Classifier ===============================================================================================
    USE_UNIFIED_CLASSIFIER: bool = Field(default=False, description="Use unified classifier node (merge intent + entity into single LLM call)")

    # Query Decomposition ==============================================================================================
    USE_QUERY_DECOMPOSITION: bool = Field(default=False, description="Enable query decomposition architecture (parallel sub-query execution)")

    # LLM Query Router =================================================================================================
    LLM_QUERY_ROUTER_MODEL: str = Field(default="gpt-4o-mini", description="Model for LLM query complexity classification")
    LLM_QUERY_ROUTER_PROVIDER: str = Field(default="openai", description="Provider for LLM query routing (openai, anthropic, google)")

    # LLM Concurrency ==================================================================================================
    LLM_MAX_CONCURRENT_ANTHROPIC: int = Field(default=8, description="Max concurrent Anthropic API calls per worker")
    LLM_MAX_CONCURRENT_OPENAI: int = Field(default=10, description="Max concurrent OpenAI API calls per worker")

    # WORKER
    REDIS_CACHING_INDEX: int = Field(default=0, description="Redis index for caching")
    REDIS_TASK_INDEX: int = Field(default=1, description="Redis index for worker tasks")
    REDIS_STREAM_INDEX: int = Field(default=2, description="Redis index for streaming")
    REDIS_TASK_RESULT_INDEX: int = Field(default=3, description="Redis index for worker tasks results")

    # Pydantic v2 설정
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }

    # Pydantic v2 field_validator 사용
    @field_validator('logger_level')
    @classmethod
    def validate_logger_level(cls, v: Optional[str]) -> Optional[str]:
        if v and v.upper() not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError('logger_level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL')
        return v.upper() if v else v

    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError('port must be between 1 and 65535')
        return v

    # Pydantic v2 model_validator 사용
    @model_validator(mode='after')
    def validate_required_settings(self) -> 'Settings':
        """개발 환경에서 필수 설정 검증"""
        if self.railway_environment == "development":
            warnings = []

            if not self.database_url:
                warnings.append("DATABASE_URL이 설정되지 않았습니다.")

            if not any([self.anthropic_api_key, self.openai_api_key, self.google_api_key, self.pplx_api_key]):
                warnings.append("LLM API 키가 하나도 설정되지 않았습니다.")

            if warnings:
                # 개발환경에서는 경고만 출력하고 실행 계속
                for warning in warnings:
                    print(f"Configuration Warning: {warning}")
                print("Please check your .env file and ensure all required variables are set.")

        return self

    @computed_field
    @property
    def available_llms(self) -> set[LLMProvider]:
        """Determine available LLM services based on provided API keys."""
        available = set()

        if self.openai_api_key:
            available.add(LLMProvider.OPENAI)
        if self.anthropic_api_key:
            available.add(LLMProvider.ANTHROPIC)
        if self.google_api_key:
            available.add(LLMProvider.GOOGLE)
        if self.pplx_api_key:
            available.add(LLMProvider.PERPLEXITY)
        if self.xai_api_key:
            available.add(LLMProvider.GROK)

        return available

    def log_startup_info(self):
        """Railway 배포 시 설정 정보 로깅"""
        is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT"))

    def setup_logger(self, name: str = "app") -> logging.Logger:
        if self.railway_environment == "development":
            level = logging.DEBUG
        elif self.logger_level:
            level = self.logger_level
        logger = logging.getLogger(name)
        if not logger.handlers:  # Prevent duplicate handlers on reload
            logger.setLevel(level)
            handler = logging.StreamHandler()
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.propagate = False
        return logger


# 설정 인스턴스 생성
settings = Settings()

# External API 키들을 os.environ에 자동 설정 (GoogleSerperAPIWrapper 등 호환성)
if settings.SERPER_API_KEY:
    os.environ['SERPER_API_KEY'] = settings.SERPER_API_KEY
if settings.KRX_API_KEY:
    os.environ['KRX_API_KEY'] = settings.KRX_API_KEY
if settings.FMP_API_KEY:
    os.environ['FMP_API_KEY'] = settings.FMP_API_KEY
if settings.MARKETSTACK_API_KEY:
    os.environ['MARKETSTACK_API_KEY'] = settings.MARKETSTACK_API_KEY
if settings.GOOGLE_CSE_ID:
    os.environ['GOOGLE_CSE_ID'] = settings.GOOGLE_CSE_ID
if settings.GOOGLE_CSE_API_KEY:
    os.environ['GOOGLE_CSE_API_KEY'] = settings.GOOGLE_CSE_API_KEY
if settings.openai_api_key:
    os.environ['OPENAI_API_KEY'] = settings.openai_api_key
if settings.google_api_key:
    os.environ['GOOGLE_API_KEY'] = settings.google_api_key
if settings.DART_API_KEY:
    os.environ['DART_API_KEY'] = settings.DART_API_KEY
if settings.NAVER_CLIENT_ID:
    os.environ['NAVER_CLIENT_ID'] = settings.NAVER_CLIENT_ID
if settings.NAVER_CLIENT_SECRET:
    os.environ['NAVER_CLIENT_SECRET'] = settings.NAVER_CLIENT_SECRET

# 기존 코드 호환성을 위한 logger 인스턴스
def setup_logger(name: str = "app") -> logging.Logger:
    """기존 코드와의 호환성을 위한 logger 설정"""
    if settings.railway_environment == "development":
        level = logging.DEBUG
    elif settings.logger_level:
        level = getattr(logging, settings.logger_level.upper(), logging.INFO)
    else:
        level = logging.INFO

    logger = logging.getLogger(name)
    if not logger.handlers:  # 중복 핸들러 방지
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# 기존 코드 호환성을 위한 logger 전역 변수
logger = setup_logger('app')

# DB 클라이언트 생성
pg_client = create_pg_client(settings)
# celery_client = create_celery_client(settings)  # 임시 주석처리
cache_redis, stream_redis, task_redis = create_redis_clients(settings)

# 시작 시 설정 정보 로깅
settings.log_startup_info()
