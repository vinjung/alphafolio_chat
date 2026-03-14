# api/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from routers import chat, chat_history, chat_integrated
from config import settings, cache_redis
from database import db
from db import close_pg_client, close_redis_clients
from core.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
import logging
import os

logging.basicConfig(level=logging.INFO)


async def _clear_stock_cache():
    """Clear stale stock cache on service startup (deployment/restart)"""
    try:
        if cache_redis:
            keys = await cache_redis.keys("stock_cache:*")
            if keys:
                deleted = await cache_redis.delete(*keys)
                logging.info(f"[Startup] Cleared {deleted} cached stock responses")
            else:
                logging.info("[Startup] No stock cache to clear")
    except Exception as e:
        logging.warning(f"[Startup] Cache clear failed (non-critical): {e}")


# Railway 포트 디버깅
railway_port = os.getenv("PORT")
config_port = settings.port
logging.info(f"Railway PORT env var: {railway_port}")
logging.info(f"Config port: {config_port}")

# Lifespan 이벤트 핸들러 (최신 방식)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup 이벤트
    await db.connect()
    await _clear_stock_cache()
    yield
    # Shutdown 이벤트
    await close_pg_client()
    await close_redis_clients()
    await db.disconnect()

app = FastAPI(
    title="Chat API",
    description="Direct Streaming Chat API",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting (slowapi)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 프로덕션에서는 간단한 422 처리 (상세 로깅 제거)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """422 Unprocessable Entity 에러 처리"""
    if settings.railway_environment == "development":
        # 개발환경에서만 상세 로깅
        logging.error(f"422 Validation Error at {request.url}")
        for error in exc.errors():
            logging.error(f"  - Field: {error.get('loc')}, Error: {error.get('msg')}")

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": exc.errors() if settings.railway_environment == "development" else "Invalid request format"
        }
    )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(chat_history.router, tags=["Chat History"])
app.include_router(chat_integrated.router, tags=["Chat Integrated"])

@app.get("/")
async def root():
    return {"message": "Chat API is running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.railway_environment,
        "port": settings.port,
        "railway_port_env": os.getenv("PORT"),
        "is_railway": bool(os.getenv("RAILWAY_ENVIRONMENT"))
    }

@app.get("/test")
async def test():
    return {"message": "FastAPI test endpoint working", "timestamp": "2025-06-25"}

@app.get("/ping")
async def ping():
    return {"status": "pong"}

@app.post("/echo")
async def echo(data: dict):
    return {"received": data, "echo": True}

if __name__ == "__main__":
    import uvicorn
    # 개발 환경: reload=True
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)

    # 프로덕션 환경 권장: workers 사용 (아래 명령어로 실행)
    # uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
