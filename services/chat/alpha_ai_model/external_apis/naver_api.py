# services/chat/alpha_ai_model/external_apis/naver_api.py
"""
Naver Search API Integration

Provides news and blog search functionality using Naver's Open API.
Specialized for Korean language content and Korean stock market news.

API Documentation: https://developers.naver.com/docs/serviceapi/search/news/news.md
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from config import settings, logger

from .base import BaseExternalAPI, APIResponse, APIErrorCode


class NaverAPI(BaseExternalAPI):
    """
    Naver Search API client

    Supports:
    - News search (뉴스 검색)
    - Blog search (블로그 검색)

    Rate Limits:
    - 25,000 requests/day
    - 1,000 requests/second (burst)
    """

    # Naver API endpoints
    BASE_URL = "https://openapi.naver.com/v1/search"
    NEWS_ENDPOINT = f"{BASE_URL}/news.json"
    BLOG_ENDPOINT = f"{BASE_URL}/blog.json"

    # Search result limits
    MAX_DISPLAY = 100  # Max results per request
    DEFAULT_DISPLAY = 10

    def __init__(self):
        """Initialize Naver API client"""
        super().__init__("NaverAPI")
        self.client_id = settings.NAVER_CLIENT_ID or ""
        self.client_secret = settings.NAVER_CLIENT_SECRET or ""

    @property
    def is_available(self) -> bool:
        """Check if Naver API is configured"""
        return bool(self.client_id and self.client_secret)

    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Accept": "application/json"
        }

    async def search(
        self,
        query: str,
        search_type: str = "news",
        display: int = 10,
        start: int = 1,
        sort: str = "sim"
    ) -> APIResponse:
        """
        Search Naver for news or blog posts

        Args:
            query: Search query
            search_type: Type of search ("news" or "blog")
            display: Number of results (1-100)
            start: Start position (1-1000)
            sort: Sort order ("sim" for relevance, "date" for date)

        Returns:
            APIResponse with search results
        """
        # Check availability
        error_response = self._check_availability(query)
        if error_response:
            return error_response

        try:
            # Select endpoint
            endpoint = self.NEWS_ENDPOINT if search_type == "news" else self.BLOG_ENDPOINT

            # Validate parameters
            display = min(max(1, display), self.MAX_DISPLAY)
            start = min(max(1, start), 1000)

            params = {
                "query": query,
                "display": display,
                "start": start,
                "sort": sort
            }

            logger.info(f"[NaverAPI] Searching {search_type}: {query}")

            # Make request
            response = await self._make_request(
                method="GET",
                url=endpoint,
                headers=self._get_headers(),
                params=params
            )

            # Parse response
            items = response.get("items", [])
            total = response.get("total", 0)

            # Log response details for debugging
            logger.debug(f"[NaverAPI] Response total={total}, items_count={len(items)}")

            # Format results
            results = self._format_results(items, search_type)

            return APIResponse.success_response(
                source=self.api_name,
                data=results,
                query=query,
                metadata={
                    "total": total,
                    "display": display,
                    "start": start,
                    "search_type": search_type,
                    "sort": sort
                }
            )

        except Exception as e:
            logger.error(f"[NaverAPI] Search failed: {e}")
            return self._handle_error(e, query)

    async def search_news(
        self,
        query: str,
        display: int = 10,
        sort: str = "date"
    ) -> APIResponse:
        """
        Search news articles

        Args:
            query: Search query
            display: Number of results
            sort: Sort order ("sim" or "date")

        Returns:
            APIResponse with news articles
        """
        return await self.search(
            query=query,
            search_type="news",
            display=display,
            sort=sort
        )

    async def search_blog(
        self,
        query: str,
        display: int = 10,
        sort: str = "sim"
    ) -> APIResponse:
        """
        Search blog posts

        Args:
            query: Search query
            display: Number of results
            sort: Sort order

        Returns:
            APIResponse with blog posts
        """
        return await self.search(
            query=query,
            search_type="blog",
            display=display,
            sort=sort
        )

    async def search_stock_news(
        self,
        stock_name: str,
        display: int = 10
    ) -> APIResponse:
        """
        Search news for a specific stock

        Args:
            stock_name: Stock name (e.g., "삼성전자")
            display: Number of results

        Returns:
            APIResponse with stock news
        """
        # Add stock-related keywords for better relevance
        query = f"{stock_name} 주가"
        return await self.search_news(query=query, display=display, sort="date")

    async def search_market_news(
        self,
        topic: str = "증시",
        display: int = 10
    ) -> APIResponse:
        """
        Search general market news

        Args:
            topic: Market topic (e.g., "증시", "코스피", "나스닥")
            display: Number of results

        Returns:
            APIResponse with market news
        """
        return await self.search_news(query=topic, display=display, sort="date")

    def _format_results(
        self,
        items: List[Dict[str, Any]],
        search_type: str
    ) -> List[Dict[str, Any]]:
        """
        Format Naver API results to standardized format

        Args:
            items: Raw API response items
            search_type: Type of search (news/blog)

        Returns:
            Formatted results list
        """
        results = []

        for item in items:
            formatted = {
                "title": self._clean_html(item.get("title", "")),
                "description": self._clean_html(item.get("description", "")),
                "link": item.get("link", ""),
                "original_link": item.get("originallink", item.get("link", "")),
                "pub_date": self._parse_date(item.get("pubDate", "")),
                "source_type": search_type
            }

            # Add blog-specific fields
            if search_type == "blog":
                formatted["blogger_name"] = item.get("bloggername", "")
                formatted["blogger_link"] = item.get("bloggerlink", "")

            results.append(formatted)

        return results

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        clean = clean.replace("&quot;", '"')
        clean = clean.replace("&amp;", "&")
        clean = clean.replace("&lt;", "<")
        clean = clean.replace("&gt;", ">")
        clean = clean.replace("&nbsp;", " ")
        return clean.strip()

    def _parse_date(self, date_str: str) -> str:
        """
        Parse Naver date format to ISO format

        Args:
            date_str: Date string (e.g., "Mon, 30 Dec 2024 10:00:00 +0900")

        Returns:
            ISO format date string
        """
        if not date_str:
            return ""

        try:
            # Naver uses RFC 2822 format
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except Exception:
            return date_str
