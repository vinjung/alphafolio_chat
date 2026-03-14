# services/chat/alpha_ai_model/graph/nodes/external_data_fetcher.py
"""
External Data Fetcher Node

Fetches data from external APIs (Naver, Serper, DART) based on routing decision.
Uses SearchStrategy for cross-market search orchestration.
"""
import asyncio
import re
from typing import Dict, Any, List, Optional
from config import logger

from ...external_apis import (
    SearchStrategy,
    NaverAPI,
    SerperAPI,
    DartAPI,
    Market,
    APIResponse
)
from ...prompts.analysis_prompts import analyze_news_sentiment


# Global API instances (lazy initialization)
_search_strategy: Optional[SearchStrategy] = None
_naver_api: Optional[NaverAPI] = None
_serper_api: Optional[SerperAPI] = None
_dart_api: Optional[DartAPI] = None


def get_search_strategy() -> SearchStrategy:
    """Get or create SearchStrategy instance"""
    global _search_strategy
    if _search_strategy is None:
        _search_strategy = SearchStrategy()
    return _search_strategy


def get_naver_api() -> NaverAPI:
    """Get or create NaverAPI instance"""
    global _naver_api
    if _naver_api is None:
        _naver_api = NaverAPI()
    return _naver_api


def get_serper_api() -> SerperAPI:
    """Get or create SerperAPI instance"""
    global _serper_api
    if _serper_api is None:
        _serper_api = SerperAPI()
    return _serper_api


def get_dart_api() -> DartAPI:
    """Get or create DartAPI instance"""
    global _dart_api
    if _dart_api is None:
        _dart_api = DartAPI()
    return _dart_api


def extract_stock_info(entities: Dict[str, Any]) -> tuple:
    """
    Extract stock code and name from entities

    Args:
        entities: Extracted entities

    Returns:
        Tuple of (stock_code, stock_name)
    """
    stock_codes = entities.get("stock_codes", [])
    stock_names = entities.get("stock_names", [])

    stock_code = stock_codes[0] if stock_codes else None
    stock_name = stock_names[0] if stock_names else None

    return stock_code, stock_name


# Korean preferred stock suffixes
_PREFERRED_SUFFIX_PATTERN = re.compile(
    r'(\d*우[A-Z]?|우선주)$'
)


def _strip_preferred_suffix(name: str) -> str:
    """Strip Korean preferred stock suffixes for better news search.

    Examples:
        '미래에셋증권2우B' -> '미래에셋증권'
        '삼성전자우' -> '삼성전자'
        'LG화학우' -> 'LG화학'
        '삼성전자' -> '삼성전자' (unchanged)
    """
    if not name:
        return name
    stripped = _PREFERRED_SUFFIX_PATTERN.sub('', name)
    return stripped if stripped else name


def _convert_preferred_code(code: str, name: str) -> str:
    """Convert Korean preferred stock code to common stock code.

    Korean preferred stocks typically end with non-0 digit (e.g. 5)
    while common stocks end with 0.

    Examples:
        ('005935', '삼성전자우') -> '005930'
        ('005930', '삼성전자') -> '005930' (unchanged)
        ('068270', '셀트리온') -> '068270' (unchanged, not preferred)
    """
    if not code or not name:
        return code
    # Only convert if name indicates preferred stock
    if not _PREFERRED_SUFFIX_PATTERN.search(name):
        return code
    # Korean stock codes: 6 digits, replace last digit with 0
    if len(code) == 6 and code.isdigit() and code[-1] != '0':
        converted = code[:-1] + '0'
        logger.info(f"[ExternalDataFetcher] Preferred stock code converted: {code} -> {converted}")
        return converted
    return code


def generate_comprehensive_queries(stock_name: str, message: str) -> List[str]:
    """
    Generate multiple search queries for comprehensive data collection

    Args:
        stock_name: Stock name
        message: Original user message

    Returns:
        List of search queries
    """
    if not stock_name:
        return [message]

    queries = []
    message_lower = message.lower()

    # Base query - stock name + news
    queries.append(f"{stock_name} 최신 뉴스")

    # Risk-related queries
    risk_keywords = ["리스크", "위험", "요인", "risk", "문제점", "우려"]
    if any(kw in message_lower for kw in risk_keywords):
        queries.append(f"{stock_name} 리스크 위험 요인")
        queries.append(f"{stock_name} 투자 주의")

    # Community/sentiment queries
    sentiment_keywords = ["반응", "여론", "커뮤니티", "의견", "투자자"]
    if any(kw in message_lower for kw in sentiment_keywords):
        queries.append(f"{stock_name} site:cafe.naver.com")
        queries.append(f"{stock_name} 투자자 반응 의견")

    # Outlook/forecast queries
    forecast_keywords = ["전망", "분석", "리포트", "평가", "호재", "악재"]
    if any(kw in message_lower for kw in forecast_keywords):
        queries.append(f"{stock_name} 전망 분석")
        queries.append(f"{stock_name} 증권사 리포트")

    # If no specific keywords, add general analysis queries
    if len(queries) == 1:
        queries.append(f"{stock_name} 분석")
        queries.append(f"{stock_name} 이슈")

    # Limit to 4 queries to avoid too many API calls
    return queries[:4]


async def fetch_news_data(
    query: str,
    market: str,
    required_apis: List[str],
    search_scope: str,
    stock_code: str = None,
    stock_name: str = None,
    num_results: int = 10
) -> Dict[str, Any]:
    """
    Fetch news data from APIs

    Args:
        query: Search query
        market: Market type (KR/US)
        required_apis: List of APIs to use
        search_scope: Search scope
        stock_code: Stock code (optional)
        stock_name: Stock name (optional)
        num_results: Number of results per source

    Returns:
        Dict with news data from each source
    """
    results = {
        "naver": None,
        "serper": None,
        "combined": []
    }

    # Use SearchStrategy for cross-market search
    if search_scope == "cross_market":
        strategy = get_search_strategy()
        market_enum = Market.KR if market == "KR" else Market.US

        search_results = await strategy.search(
            query=query,
            market=market_enum,
            stock_code=stock_code,
            stock_name=stock_name,
            num_results=num_results
        )

        for source, response in search_results.items():
            if response.success:
                results[source] = response.data
            else:
                logger.warning(f"[ExternalDataFetcher] {source} failed: {response.error}")

        # Merge results
        results["combined"] = strategy.merge_results(search_results)

    else:
        # Single source search
        if "naver" in required_apis:
            naver = get_naver_api()
            response = await naver.search_news(query, display=num_results)

            if response.success:
                results["naver"] = response.data
                results["combined"].extend(response.data)
            else:
                logger.warning(f"[ExternalDataFetcher] Naver failed: {response.error}")

        if "serper" in required_apis:
            serper = get_serper_api()
            response = await serper.search_news(query, num=num_results)

            if response.success:
                results["serper"] = response.data
                results["combined"].extend(response.data)
            else:
                logger.warning(f"[ExternalDataFetcher] Serper failed: {response.error}")

    return results


async def fetch_disclosure_data(
    stock_name: str = None,
    stock_code: str = None,
    days: int = 30,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Fetch disclosure data from DART

    Args:
        stock_name: Stock name
        stock_code: Stock code
        days: Days to look back
        limit: Maximum results

    Returns:
        Dict with disclosure data
    """
    results = {
        "disclosures": [],
        "company_info": None
    }

    dart = get_dart_api()

    # Get disclosures
    response = await dart.get_recent_disclosures(
        corp_name=stock_name,
        days=days,
        limit=limit
    )

    if response.success:
        results["disclosures"] = response.data
    else:
        logger.warning(f"[ExternalDataFetcher] DART disclosures failed: {response.error}")

    return results


async def external_data_fetcher(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch external data based on routing decision

    Args:
        state: Current graph state with data_source and required_apis

    Returns:
        Updated state with external data
    """
    logger.info("[AlphaAI:ExternalDataFetcher] Processing...")

    message = state.get("message", "")
    market = state.get("market", "KR")
    data_source = state.get("data_source", "db_only")
    required_apis = state.get("required_apis", [])
    search_scope = state.get("search_scope", "local_only")
    entities = state.get("entities", {})

    # Skip if DB only
    if data_source == "db_only":
        logger.info("[AlphaAI:ExternalDataFetcher] Skipping - DB only mode")
        return {
            **state,
            "processing_steps": state.get("processing_steps", []) + ["external_data_fetcher_skipped"]
        }

    # Extract stock info - prefer SQL-discovered stocks over entity extractor
    sql_stock_names = entities.get("stock_names_from_sql", [])
    sql_stock_codes = entities.get("stock_codes_from_sql", [])
    if sql_stock_names:
        raw_name = sql_stock_names[0]
        stock_name = _strip_preferred_suffix(raw_name)
        raw_code = sql_stock_codes[0] if sql_stock_codes else None
        stock_code = _convert_preferred_code(raw_code, raw_name) if raw_code else None
        # Collect secondary stocks for lightweight news fetch
        secondary_stocks = []
        MAX_SECONDARY_STOCKS = 2
        for i in range(1, min(len(sql_stock_names), MAX_SECONDARY_STOCKS + 1)):
            sec_raw_name = sql_stock_names[i]
            sec_raw_code = sql_stock_codes[i] if i < len(sql_stock_codes) else None
            sec_name = _strip_preferred_suffix(sec_raw_name)
            sec_code = _convert_preferred_code(sec_raw_code, sec_raw_name) if sec_raw_code else None
            secondary_stocks.append((sec_name, sec_code))
        logger.info(
            f"[ExternalDataFetcher] Using SQL-discovered stock: {stock_name}"
            f"{f', secondary: {[s[0] for s in secondary_stocks]}' if secondary_stocks else ''}"
        )
    else:
        stock_code, stock_name = extract_stock_info(entities)
        secondary_stocks = []

    # Build search queries - use comprehensive queries for better coverage
    search_queries = generate_comprehensive_queries(stock_name, message)
    primary_query = stock_name or message

    # Initialize result containers
    news_data = []
    disclosure_data = []
    web_search_data = []
    news_sentiment = None

    # Get LLM config for sentiment analysis
    provider = state.get("provider")
    model = state.get("model_name")

    try:
        # Fetch news if needed - use multiple queries for comprehensive search
        if any(api in required_apis for api in ["naver", "serper"]):
            all_news_results = []
            seen_urls = set()  # Deduplicate by URL

            for query in search_queries:
                try:
                    news_results = await fetch_news_data(
                        query=query,
                        market=market,
                        required_apis=required_apis,
                        search_scope=search_scope,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        num_results=5  # Fewer per query, more queries
                    )
                    for item in news_results.get("combined", []):
                        url = item.get("link") or item.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            item["search_query"] = query  # Track which query found this
                            all_news_results.append(item)
                except Exception as qe:
                    logger.warning(f"[ExternalDataFetcher] Query '{query}' failed: {qe}")
                    continue

            # Fetch lightweight news for secondary stocks (1 query each, parallel)
            if secondary_stocks:
                async def _fetch_secondary(sec_name, sec_code):
                    try:
                        sec_results = await fetch_news_data(
                            query=f"{sec_name} 주가",
                            market=market,
                            required_apis=required_apis,
                            search_scope=search_scope,
                            stock_code=sec_code,
                            stock_name=sec_name,
                            num_results=3,
                        )
                        items = []
                        for item in sec_results.get("combined", []):
                            url = item.get("link") or item.get("url", "")
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                item["source_stock"] = sec_name
                                items.append(item)
                        return items
                    except Exception as se:
                        logger.warning(f"[ExternalDataFetcher] Secondary stock '{sec_name}' fetch failed: {se}")
                        return []

                sec_tasks = [_fetch_secondary(sn, sc) for sn, sc in secondary_stocks]
                sec_results_list = await asyncio.gather(*sec_tasks, return_exceptions=True)
                for sr in sec_results_list:
                    if isinstance(sr, list):
                        all_news_results.extend(sr)
                logger.info(
                    f"[ExternalDataFetcher] Secondary stocks news: "
                    f"{sum(len(sr) for sr in sec_results_list if isinstance(sr, list))} items"
                )

            logger.info(f"[ExternalDataFetcher] Multi-query search: {len(search_queries)} queries, {len(all_news_results)} unique results")
            logger.debug(f"[ExternalDataFetcher] Search queries used: {search_queries}")
            news_data = all_news_results

            # Separate web search results from collected data
            web_search_data = [
                item for item in all_news_results
                if item.get("source_type") == "web" or "site:" in item.get("search_query", "")
            ]

            # Apply sentiment analysis to news data
            if news_data:
                try:
                    sentiment_result = await analyze_news_sentiment(
                        news_items=news_data,
                        stock_name=stock_name,
                        provider=provider,
                        model=model
                    )
                    news_data = sentiment_result.get("items", news_data)
                    news_sentiment = {
                        "overall": sentiment_result.get("overall", "NEUTRAL"),
                        "confidence": sentiment_result.get("confidence", "LOW"),
                        "positive_count": sentiment_result.get("positive_count", 0),
                        "negative_count": sentiment_result.get("negative_count", 0),
                        "neutral_count": sentiment_result.get("neutral_count", 0)
                    }
                    logger.info(f"[AlphaAI:ExternalDataFetcher] Sentiment: {news_sentiment['overall']} "
                               f"(confidence: {news_sentiment['confidence']})")
                except Exception as se:
                    logger.warning(f"[AlphaAI:ExternalDataFetcher] Sentiment analysis failed: {se}")
                    # Continue without sentiment data

        # Fetch disclosures if needed
        if "dart" in required_apis:
            disclosure_results = await fetch_disclosure_data(
                stock_name=stock_name,
                stock_code=stock_code,
                days=30,
                limit=10
            )
            disclosure_data = disclosure_results.get("disclosures", [])

        logger.info(f"[AlphaAI:ExternalDataFetcher] Fetched: "
                   f"news={len(news_data)}, disclosures={len(disclosure_data)}, "
                   f"web={len(web_search_data)}")

    except Exception as e:
        logger.error(f"[AlphaAI:ExternalDataFetcher] Error: {e}")
        # Continue with empty results rather than failing

    return {
        **state,
        "news_data": news_data,
        "disclosure_data": disclosure_data,
        "web_search_data": web_search_data,
        "news_sentiment": news_sentiment,
        "processing_steps": state.get("processing_steps", []) + ["external_data_fetcher"]
    }
