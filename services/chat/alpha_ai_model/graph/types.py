# services/chat/alpha_ai_model/graph/types.py
"""
Alpha AI Graph State Type Definitions
"""
from typing import TypedDict, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage


class AlphaAIGraphState(TypedDict):
    """
    State object for Alpha AI LangGraph workflow

    Flow: message -> intent -> entities -> schema -> sql -> result -> response
    """
    # Input
    message: str
    user_id: Optional[str]
    session_id: Optional[str]

    # LLM Configuration
    provider: Optional[str]
    model_name: Optional[str]
    model_config: Optional[Dict[str, Any]]

    # Message History
    messages: List[BaseMessage]

    # Intent Classification
    intent: Optional[str]  # query, ranking, filter, analysis, comparison, etc.
    market: Optional[str]  # KR, US

    # Entity Extraction
    entities: Optional[Dict[str, Any]]
    # Expected structure:
    # {
    #     "stock_names": ["Samsung Electronics", "Apple"],
    #     "stock_codes": ["005930", "AAPL"],
    #     "indicators": ["RSI", "MACD"],
    #     "conditions": {"rsi": {"op": "<", "value": 30}},
    #     "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
    #     "limit": 10,
    #     "order_by": "trading_value",
    #     "order_direction": "DESC"
    # }

    # RAG Results
    relevant_tables: Optional[List[str]]
    relevant_columns: Optional[List[Dict[str, str]]]
    # Structure: [{"table": "kr_intraday", "column": "trading_value", "description": "..."}]
    few_shot_examples: Optional[List[Dict[str, str]]]
    # Structure: [{"question": "...", "sql": "...", "category": "ranking"}]

    # SQL Generation
    sql_model_used: Optional[str]  # Track which model generated the SQL
    generated_sql: Optional[str]
    sql_valid: Optional[bool]
    sql_error: Optional[str]
    sql_retry_count: Optional[int]
    needs_regeneration: Optional[bool]  # Flag for retry loop
    empty_result_retry: Optional[bool]  # Flag to retry with Claude when fine-tuned returned 0 rows
    schema_context: Optional[str]  # Schema context for SQL correction

    # Execution Results
    query_result: Optional[List[Dict[str, Any]]]
    result_count: Optional[int]
    execution_time_ms: Optional[float]

    # Response
    response: Optional[str]
    response_type: Optional[str]  # table, text, chart, error

    # Data Source Routing (Phase 5)
    data_source: Optional[str]  # "db_only", "external_only", "hybrid"
    required_apis: Optional[List[str]]  # ["naver", "serper", "dart"]
    search_scope: Optional[str]  # "local_only", "global_only", "cross_market"

    # External Data (Phase 5)
    news_data: Optional[List[Dict[str, Any]]]  # News search results
    disclosure_data: Optional[List[Dict[str, Any]]]  # DART disclosure data
    web_search_data: Optional[List[Dict[str, Any]]]  # Web search results

    # Hybrid Analysis (Phase 5)
    hybrid_analysis: Optional[str]  # Combined analysis result
    requires_disclaimer: Optional[bool]  # Whether disclaimer is needed
    disclaimer_type: Optional[str]  # "investment", "forecast", etc.

    # Visualization (for frontend chart/table rendering)
    # Supported types: table, line_chart, bar_chart, candlestick, pie_chart
    visualization: Optional[Dict[str, Any]]

    # Supplementary Charts (technical indicator charts built post-query)
    supplementary_charts: Optional[Dict[str, Any]]
    # Structure examples:
    # {
    #     "type": "table",
    #     "title": "RSI 30 이하 종목",
    #     "data": {
    #         "headers": ["종목코드", "종목명", "현재가", ...],
    #         "rows": [["005930", "삼성전자", 71000, ...], ...]
    #     }
    # }
    # {
    #     "type": "line_chart",
    #     "title": "삼성전자 주가 추이",
    #     "data": {
    #         "labels": ["01/01", "01/02", ...],
    #         "datasets": [{"label": "종가", "data": [75000, 75500, ...]}]
    #     }
    # }
    # {
    #     "type": "candlestick",
    #     "title": "삼성전자 일봉 차트",
    #     "data": {
    #         "labels": ["01/01", "01/02", ...],
    #         "datasets": [{"data": [{"open": 100, "high": 110, "low": 95, "close": 105}, ...]}]
    #     }
    # }

    # Context Enrichment
    supplementary_context: Optional[str]  # Structured supplementary analysis context

    # Query Decomposition (feature flag: USE_QUERY_DECOMPOSITION)
    sub_queries: Optional[List[Dict[str, Any]]]
    # Structure: [{"question": str, "market": str, "tables": [str], "depends_on": int|None}]
    # Max 7 sub-queries per request

    sub_query_results: Optional[List[Dict[str, Any]]]
    # Structure: [{"question": str, "sql": str, "result": [dict], "result_count": int, "error": str|None}]
    # Includes all sub-query results (success and failure)

    # Query Router (feature flag: USE_QUERY_DECOMPOSITION)
    query_route: Optional[str]  # "simple" | "complex" | "chat" | "external"

    # Metadata
    processing_steps: Optional[List[str]]
    total_tokens_used: Optional[int]
