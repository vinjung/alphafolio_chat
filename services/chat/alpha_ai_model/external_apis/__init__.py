# services/chat/alpha_ai_model/external_apis/__init__.py
"""
External APIs for Alpha AI

Provides integrations with external data sources:
- NaverAPI: Korean news and blog search
- SerperAPI: Google web and news search
- DartAPI: Korean corporate disclosures
- SearchStrategy: Cross-market search orchestration
"""
from .base import BaseExternalAPI, APIResponse, APIErrorCode
from .naver_api import NaverAPI
from .serper_api import SerperAPI
from .dart_api import DartAPI
from .search_strategy import SearchStrategy, SearchScope, SearchPlan, Market

__all__ = [
    # Base classes
    "BaseExternalAPI",
    "APIResponse",
    "APIErrorCode",

    # API implementations
    "NaverAPI",
    "SerperAPI",
    "DartAPI",

    # Search strategy
    "SearchStrategy",
    "SearchScope",
    "SearchPlan",
    "Market"
]
