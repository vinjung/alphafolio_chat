# services/chat/alpha_ai_model/external_apis/serper_api.py
"""
Serper API Integration

Provides Google Search functionality via Serper.dev API.
Specialized for English content and global market news.

API Documentation: https://serper.dev/docs
"""
from typing import Dict, Any, List, Optional
from config import settings, logger

from .base import BaseExternalAPI, APIResponse, APIErrorCode


class SerperAPI(BaseExternalAPI):
    """
    Serper API client for Google Search

    Supports:
    - Web search
    - News search
    - Image search

    Rate Limits:
    - Depends on plan (free tier: 2,500 queries/month)
    """

    # Serper API endpoint
    BASE_URL = "https://google.serper.dev"
    SEARCH_ENDPOINT = f"{BASE_URL}/search"
    NEWS_ENDPOINT = f"{BASE_URL}/news"
    IMAGES_ENDPOINT = f"{BASE_URL}/images"

    # Default settings
    DEFAULT_NUM_RESULTS = 10
    MAX_RESULTS = 100

    def __init__(self):
        """Initialize Serper API client"""
        super().__init__("SerperAPI")
        self.api_key = settings.SERPER_API_KEY or ""

    @property
    def is_available(self) -> bool:
        """Check if Serper API is configured"""
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    async def search(
        self,
        query: str,
        search_type: str = "search",
        num: int = 10,
        gl: str = "us",
        hl: str = "en",
        **kwargs
    ) -> APIResponse:
        """
        Search Google via Serper

        Args:
            query: Search query
            search_type: Type of search ("search", "news", "images")
            num: Number of results (1-100)
            gl: Geographic location (country code)
            hl: Language code
            **kwargs: Additional parameters

        Returns:
            APIResponse with search results
        """
        # Check availability
        error_response = self._check_availability(query)
        if error_response:
            return error_response

        try:
            # Select endpoint
            endpoint_map = {
                "search": self.SEARCH_ENDPOINT,
                "news": self.NEWS_ENDPOINT,
                "images": self.IMAGES_ENDPOINT
            }
            endpoint = endpoint_map.get(search_type, self.SEARCH_ENDPOINT)

            # Validate parameters
            num = min(max(1, num), self.MAX_RESULTS)

            payload = {
                "q": query,
                "num": num,
                "gl": gl,
                "hl": hl
            }
            payload.update(kwargs)

            logger.info(f"[SerperAPI] Searching ({search_type}): {query}")

            # Make request
            response = await self._make_request(
                method="POST",
                url=endpoint,
                headers=self._get_headers(),
                json_data=payload
            )

            # Parse response based on search type
            if search_type == "news":
                results = self._format_news_results(response)
            elif search_type == "images":
                results = self._format_image_results(response)
            else:
                results = self._format_search_results(response)

            return APIResponse.success_response(
                source=self.api_name,
                data=results,
                query=query,
                metadata={
                    "search_type": search_type,
                    "num_requested": num,
                    "num_returned": len(results),
                    "gl": gl,
                    "hl": hl,
                    "search_parameters": response.get("searchParameters", {})
                }
            )

        except Exception as e:
            logger.error(f"[SerperAPI] Search failed: {e}")
            return self._handle_error(e, query)

    async def search_web(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
        hl: str = "en"
    ) -> APIResponse:
        """
        Perform web search

        Args:
            query: Search query
            num: Number of results
            gl: Geographic location
            hl: Language

        Returns:
            APIResponse with web search results
        """
        return await self.search(
            query=query,
            search_type="search",
            num=num,
            gl=gl,
            hl=hl
        )

    async def search_news(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
        hl: str = "en",
        tbs: str = None
    ) -> APIResponse:
        """
        Search news articles

        Args:
            query: Search query
            num: Number of results
            gl: Geographic location
            hl: Language
            tbs: Time-based search (e.g., "qdr:d" for past day, "qdr:w" for past week)

        Returns:
            APIResponse with news results
        """
        kwargs = {}
        if tbs:
            kwargs["tbs"] = tbs

        return await self.search(
            query=query,
            search_type="news",
            num=num,
            gl=gl,
            hl=hl,
            **kwargs
        )

    async def search_stock_news(
        self,
        symbol: str,
        company_name: str = None,
        num: int = 10
    ) -> APIResponse:
        """
        Search news for a specific stock

        Args:
            symbol: Stock symbol (e.g., "AAPL", "NVDA")
            company_name: Company name for better results
            num: Number of results

        Returns:
            APIResponse with stock news
        """
        if company_name:
            query = f"{company_name} ({symbol}) stock news"
        else:
            query = f"{symbol} stock news"

        return await self.search_news(query=query, num=num)

    async def search_korean_stock_global(
        self,
        stock_name_en: str,
        num: int = 10
    ) -> APIResponse:
        """
        Search global news for Korean stock (cross-market)

        Args:
            stock_name_en: English name of Korean stock (e.g., "Samsung Electronics")
            num: Number of results

        Returns:
            APIResponse with global news about Korean stock
        """
        query = f"{stock_name_en} stock analysis"
        return await self.search_news(query=query, num=num, gl="us", hl="en")

    async def search_market_analysis(
        self,
        topic: str,
        num: int = 10
    ) -> APIResponse:
        """
        Search market analysis articles

        Args:
            topic: Market topic (e.g., "AI semiconductor", "Fed interest rate")
            num: Number of results

        Returns:
            APIResponse with market analysis
        """
        query = f"{topic} market analysis"
        return await self.search_web(query=query, num=num)

    def _format_search_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format web search results

        Args:
            response: Raw API response

        Returns:
            Formatted results list
        """
        results = []

        # Organic results
        for item in response.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "position": item.get("position", 0),
                "source_type": "web",
                "displayed_link": item.get("displayedLink", "")
            })

        return results

    def _format_news_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format news search results

        Args:
            response: Raw API response

        Returns:
            Formatted news results list
        """
        results = []

        for item in response.get("news", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "source": item.get("source", ""),
                "date": item.get("date", ""),
                "image_url": item.get("imageUrl", ""),
                "source_type": "news"
            })

        return results

    def _format_image_results(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format image search results

        Args:
            response: Raw API response

        Returns:
            Formatted image results list
        """
        results = []

        for item in response.get("images", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "image_url": item.get("imageUrl", ""),
                "thumbnail_url": item.get("thumbnailUrl", ""),
                "source": item.get("source", ""),
                "source_type": "image"
            })

        return results
