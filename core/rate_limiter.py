# core/rate_limiter.py
"""
Rate limiter instance for FastAPI endpoints using slowapi.

Separated from main.py to avoid circular imports
(main.py imports routers, routers import limiter).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
