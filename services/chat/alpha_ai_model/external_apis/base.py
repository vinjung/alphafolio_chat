# services/chat/alpha_ai_model/external_apis/base.py
"""
Base External API Class

Abstract base class for all external API integrations.
Implements Graceful Degradation pattern for error handling.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp
import asyncio
from config import logger


class APIErrorCode(str, Enum):
    """Standard error codes for API responses"""
    SUCCESS = "SUCCESS"
    API_NOT_CONFIGURED = "API_NOT_CONFIGURED"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    NOT_FOUND = "NOT_FOUND"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class APIResponse:
    """
    Standardized API response structure for Graceful Degradation

    Attributes:
        success: Whether the API call succeeded
        data: Response data (results, items, etc.)
        error: Error message if failed
        error_code: Standardized error code
        source: API source name (naver, serper, dart, etc.)
        query: Original query/request
        metadata: Additional metadata (count, page, etc.)
        timestamp: Response timestamp
    """
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    error_code: Optional[APIErrorCode] = None
    source: str = ""
    query: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code.value if self.error_code else None,
            "source": self.source,
            "query": self.query,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def not_configured(cls, source: str, query: str = "") -> "APIResponse":
        """Create a 'not configured' response"""
        return cls(
            success=False,
            error=f"{source} API is not configured",
            error_code=APIErrorCode.API_NOT_CONFIGURED,
            source=source,
            query=query
        )

    @classmethod
    def error_response(
        cls,
        source: str,
        error: str,
        error_code: APIErrorCode = APIErrorCode.UNKNOWN_ERROR,
        query: str = ""
    ) -> "APIResponse":
        """Create an error response"""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            source=source,
            query=query
        )

    @classmethod
    def success_response(
        cls,
        source: str,
        data: List[Dict[str, Any]],
        query: str = "",
        metadata: Dict[str, Any] = None
    ) -> "APIResponse":
        """Create a success response"""
        return cls(
            success=True,
            data=data,
            error_code=APIErrorCode.SUCCESS,
            source=source,
            query=query,
            metadata=metadata or {}
        )


class BaseExternalAPI(ABC):
    """
    Abstract base class for external API integrations

    All external APIs should inherit from this class and implement
    the required abstract methods.

    Features:
    - Graceful Degradation: Returns structured response even on failure
    - Rate limiting awareness
    - Timeout handling
    - Retry logic with exponential backoff
    """

    # Default configuration
    DEFAULT_TIMEOUT = 10  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self, api_name: str):
        """
        Initialize base API

        Args:
            api_name: Name of the API (for logging and response source)
        """
        self.api_name = api_name
        self._session: Optional[aiohttp.ClientSession] = None
        logger.info(f"[{self.api_name}] Initialized")

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if API is configured and available"""
        pass

    @abstractmethod
    async def search(self, query: str, **kwargs) -> APIResponse:
        """
        Perform a search query

        Args:
            query: Search query string
            **kwargs: Additional search parameters

        Returns:
            APIResponse with search results or error
        """
        pass

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.DEFAULT_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            params: Query parameters
            json_data: JSON body data
            retry: Whether to retry on failure

        Returns:
            Response data as dictionary

        Raises:
            Various exceptions on failure
        """
        session = await self._get_session()
        last_error = None

        for attempt in range(self.MAX_RETRIES if retry else 1):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data
                ) as response:
                    if response.status == 429:  # Rate limited
                        wait_time = int(response.headers.get("Retry-After", self.RETRY_DELAY * (attempt + 1)))
                        logger.warning(f"[{self.api_name}] Rate limited, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue

                    if response.status == 401 or response.status == 403:
                        raise PermissionError("Authentication failed")

                    if response.status >= 400:
                        text = await response.text()
                        raise aiohttp.ClientResponseError(
                            response.request_info,
                            response.history,
                            status=response.status,
                            message=text
                        )

                    return await response.json()

            except asyncio.TimeoutError:
                last_error = "Request timed out"
                logger.warning(f"[{self.api_name}] Timeout (attempt {attempt + 1}/{self.MAX_RETRIES})")

            except aiohttp.ClientError as e:
                last_error = str(e)
                logger.warning(f"[{self.api_name}] Client error: {e} (attempt {attempt + 1}/{self.MAX_RETRIES})")

            if attempt < self.MAX_RETRIES - 1:
                await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

        raise Exception(last_error or "Request failed after retries")

    def _check_availability(self, query: str = "") -> Optional[APIResponse]:
        """
        Check if API is available, return error response if not

        Args:
            query: Original query for error response

        Returns:
            None if available, APIResponse error if not
        """
        if not self.is_available:
            logger.warning(f"[{self.api_name}] API not configured")
            return APIResponse.not_configured(self.api_name, query)
        return None

    def _handle_error(
        self,
        error: Exception,
        query: str = ""
    ) -> APIResponse:
        """
        Handle exception and return appropriate APIResponse

        Args:
            error: The exception that occurred
            query: Original query

        Returns:
            APIResponse with error details
        """
        error_str = str(error)

        if "timed out" in error_str.lower() or isinstance(error, asyncio.TimeoutError):
            return APIResponse.error_response(
                self.api_name,
                "Request timed out",
                APIErrorCode.TIMEOUT,
                query
            )

        if isinstance(error, PermissionError) or "401" in error_str or "403" in error_str:
            return APIResponse.error_response(
                self.api_name,
                "Authentication failed",
                APIErrorCode.AUTHENTICATION_FAILED,
                query
            )

        if "429" in error_str or "rate" in error_str.lower():
            return APIResponse.error_response(
                self.api_name,
                "Rate limit exceeded",
                APIErrorCode.RATE_LIMITED,
                query
            )

        if isinstance(error, aiohttp.ClientError):
            return APIResponse.error_response(
                self.api_name,
                f"Network error: {error_str}",
                APIErrorCode.NETWORK_ERROR,
                query
            )

        logger.error(f"[{self.api_name}] Unexpected error: {error}")
        return APIResponse.error_response(
            self.api_name,
            error_str,
            APIErrorCode.UNKNOWN_ERROR,
            query
        )

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
