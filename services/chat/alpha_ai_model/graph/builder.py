# services/chat/alpha_ai_model/graph/builder.py
"""
Alpha AI LangGraph Workflow Builder

Phase 6 Enhanced Workflow (with Context Enrichment):
START -> intent_classifier -> [conditional]
    - chat -> data_source_router -> external_data_fetcher -> response_generator -> END
    - query/ranking/filter/etc -> entity_extractor -> data_source_router -> [conditional]
        - EXTERNAL_ONLY -> external_data_fetcher -> response_generator -> END
        - DB_ONLY/HYBRID -> schema_retriever -> sql_generator -> sql_validator -> [conditional]
            - valid -> sql_executor -> context_enricher -> [conditional]
                - DB_ONLY -> response_generator -> END
                - HYBRID -> external_data_fetcher -> response_generator -> END
            - needs_regeneration -> sql_generator (retry loop)
            - max_retries -> response_generator (error) -> END

Complex-Only Query Router Workflow (USE_QUERY_DECOMPOSITION=True):
START -> query_router (rule-based, 0 LLM) -> [conditional]
    - chat/explain -> response_generator -> END
    - external -> external_data_fetcher -> response_generator -> END
    - complex -> query_decomposer -> parallel_sql_pipeline -> context_enricher -> [conditional]
        - hybrid -> external_data_fetcher_hybrid -> response_generator -> END
        - db_only -> response_generator -> END
"""
from langgraph.graph import StateGraph, START, END
from .types import AlphaAIGraphState
from config import settings

# Import nodes
from .nodes import (
    intent_classifier,
    entity_extractor,
    schema_retriever,
    sql_generator,
    sql_validator,
    sql_executor,
    response_generator,
    # Phase 5 nodes
    data_source_router,
    external_data_fetcher,
    # Phase 6 nodes
    context_enricher,
    # Unified classifier (feature flag)
    unified_classifier,
    # Query Decomposition (feature flag)
    query_decomposer,
    parallel_sql_pipeline,
    # Query Router - hybrid simple/complex routing
    query_router,
)


def route_after_intent(state: AlphaAIGraphState) -> str:
    """
    Route based on intent classification result

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    intent = state.get("intent", "")

    # General chat and explain intents go to data source router (skip SQL pipeline)
    # These intents are handled directly by LLM without database queries
    if intent in ["chat", "explain"]:
        return "data_source_router_chat"

    # All other intents proceed to entity extraction
    return "entity_extractor"


def route_after_data_source_chat(state: AlphaAIGraphState) -> str:
    """
    Route after data source router for chat intent

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    data_source = state.get("data_source", "db_only")

    # If external data needed, fetch it
    if data_source in ["external_only", "hybrid"]:
        return "external_data_fetcher"

    # Otherwise go directly to response
    return "response_generator"


def route_after_data_source(state: AlphaAIGraphState) -> str:
    """
    Route after data source router for SQL intents

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    data_source = state.get("data_source", "db_only")

    # External only - skip SQL pipeline
    if data_source == "external_only":
        return "external_data_fetcher"

    # DB only or Hybrid - proceed to SQL pipeline
    return "schema_retriever"


def route_after_validation(state: AlphaAIGraphState) -> str:
    """
    Route based on SQL validation result

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    # If SQL is valid, proceed to execution
    if state.get("sql_valid"):
        return "sql_executor"

    # If regeneration is needed and allowed, retry
    if state.get("needs_regeneration"):
        return "sql_generator"

    # Max retries reached or unrecoverable error, generate error response
    return "response_generator"


def route_after_executor(state: AlphaAIGraphState) -> str:
    """Route after SQL execution - retry with Claude on empty fine-tuned result"""
    if state.get("empty_result_retry"):
        return "sql_generator"
    return "context_enricher"


def route_after_execution(state: AlphaAIGraphState) -> str:
    """
    Route after SQL execution based on data source

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    data_source = state.get("data_source", "db_only")

    # Hybrid mode - need to fetch external data and analyze
    if data_source == "hybrid":
        return "external_data_fetcher_hybrid"

    # DB only - go directly to response
    return "response_generator"


def route_after_external_chat(state: AlphaAIGraphState) -> str:
    """
    Route after external data fetcher for chat

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    return "response_generator"


def route_after_unified(state: AlphaAIGraphState) -> str:
    """
    Route after unified classifier (replaces route_after_intent + entity_extractor edge).
    Entities are already extracted in the unified node.

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    intent = state.get("intent", "")

    # General chat and explain intents skip SQL pipeline
    if intent in ["chat", "explain"]:
        return "data_source_router_chat"

    # All other intents proceed directly to data_source_router (entities already extracted)
    return "data_source_router"


def route_after_query_router(state: AlphaAIGraphState) -> str:
    """
    Route based on query_router classification.

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    route = state.get("query_route", "complex")
    if route == "chat":
        return "response_generator"
    elif route == "external":
        return "external_data_fetcher"
    else:  # "complex" - all DB queries go through decomposer
        return "query_decomposer"


def route_after_decomposer(state: AlphaAIGraphState) -> str:
    """
    Route after query decomposer node.

    Routes based on intent and data_source determined by decomposer:
    - chat/explain -> response_generator (no SQL needed)
    - external_only -> external_data_fetcher (news/disclosure only)
    - db_only/hybrid -> parallel_sql_pipeline (SQL execution)

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    intent = state.get("intent", "")
    data_source = state.get("data_source", "db_only")

    if intent in ["chat", "explain"]:
        return "response_generator"
    if data_source == "external_only":
        return "external_data_fetcher"
    return "parallel_sql_pipeline"


def build_alpha_ai_graph() -> StateGraph:
    """
    Build the Alpha AI workflow graph

    Supports three modes via feature flags:
    1. USE_QUERY_DECOMPOSITION=True: Decomposition + parallel SQL pipeline
    2. USE_UNIFIED_CLASSIFIER=True: Single LLM call for intent + entity
    3. Default: Separate intent classifier + entity extractor

    Returns:
        Compiled StateGraph for Alpha AI
    """
    workflow = StateGraph(AlphaAIGraphState)

    if settings.USE_QUERY_DECOMPOSITION:
        # ================================================================
        # Complex-Only Query Router Architecture
        # query_router (rule-based, 0 LLM) -> all DB queries to complex path
        #
        # complex  -> query_decomposer -> parallel_sql_pipeline -> context_enricher
        # chat     -> response_generator
        # external -> external_data_fetcher -> response_generator
        # ================================================================

        # === Shared entry ===
        workflow.add_node("query_router", query_router)

        # === Complex path nodes ===
        workflow.add_node("query_decomposer", query_decomposer)
        workflow.add_node("parallel_sql_pipeline", parallel_sql_pipeline)

        # === Shared tail nodes ===
        workflow.add_node("context_enricher", context_enricher)
        workflow.add_node("response_generator", response_generator)
        workflow.add_node("external_data_fetcher", external_data_fetcher)
        workflow.add_node("external_data_fetcher_hybrid", external_data_fetcher)

        # === Entry point ===
        workflow.add_edge(START, "query_router")

        # === Router -> 3-way branch ===
        workflow.add_conditional_edges(
            "query_router",
            route_after_query_router,
            {
                "response_generator": "response_generator",       # chat/explain
                "external_data_fetcher": "external_data_fetcher",  # external
                "query_decomposer": "query_decomposer",           # complex
            }
        )

        # --- Complex path ---
        workflow.add_conditional_edges(
            "query_decomposer",
            route_after_decomposer,
            {
                "response_generator": "response_generator",
                "external_data_fetcher": "external_data_fetcher",
                "parallel_sql_pipeline": "parallel_sql_pipeline",
            }
        )
        workflow.add_edge("parallel_sql_pipeline", "context_enricher")

        # --- Shared tail ---
        workflow.add_conditional_edges(
            "context_enricher",
            route_after_execution,
            {
                "external_data_fetcher_hybrid": "external_data_fetcher_hybrid",
                "response_generator": "response_generator",
            }
        )
        workflow.add_edge("external_data_fetcher_hybrid", "response_generator")
        workflow.add_edge("external_data_fetcher", "response_generator")

        # Final edge
        workflow.add_edge("response_generator", END)

    else:
        # ================================================================
        # Existing Architecture (unchanged)
        # ================================================================
        # Common nodes (shared by both paths)
        workflow.add_node("schema_retriever", schema_retriever)
        workflow.add_node("sql_generator", sql_generator)
        workflow.add_node("sql_validator", sql_validator)
        workflow.add_node("sql_executor", sql_executor)
        workflow.add_node("response_generator", response_generator)

        # Phase 5 nodes (some nodes used in multiple contexts with different routing)
        workflow.add_node("data_source_router_chat", data_source_router)
        workflow.add_node("data_source_router", data_source_router)

        # Phase 6 nodes
        workflow.add_node("context_enricher", context_enricher)
        workflow.add_node("external_data_fetcher", external_data_fetcher)
        workflow.add_node("external_data_fetcher_hybrid", external_data_fetcher)

        # Feature flag: unified classifier vs separate intent + entity nodes
        if settings.USE_UNIFIED_CLASSIFIER:
            # Unified path: single LLM call for intent + entity extraction
            workflow.add_node("unified_classifier", unified_classifier)
            workflow.add_edge(START, "unified_classifier")

            workflow.add_conditional_edges(
                "unified_classifier",
                route_after_unified,
                {
                    "data_source_router": "data_source_router",
                    "data_source_router_chat": "data_source_router_chat"
                }
            )
        else:
            # Original path: separate intent classification + entity extraction
            workflow.add_node("intent_classifier", intent_classifier)
            workflow.add_node("entity_extractor", entity_extractor)

            workflow.add_edge(START, "intent_classifier")

            workflow.add_conditional_edges(
                "intent_classifier",
                route_after_intent,
                {
                    "entity_extractor": "entity_extractor",
                    "data_source_router_chat": "data_source_router_chat"
                }
            )

            # SQL path: entity_extractor -> data_source_router
            workflow.add_edge("entity_extractor", "data_source_router")

        # Chat path: data_source_router -> conditional
        workflow.add_conditional_edges(
            "data_source_router_chat",
            route_after_data_source_chat,
            {
                "external_data_fetcher": "external_data_fetcher",
                "response_generator": "response_generator"
            }
        )

        # External data for chat -> response
        workflow.add_edge("external_data_fetcher", "response_generator")

        # Conditional routing after data source router
        workflow.add_conditional_edges(
            "data_source_router",
            route_after_data_source,
            {
                "external_data_fetcher": "external_data_fetcher",
                "schema_retriever": "schema_retriever"
            }
        )

        # SQL pipeline
        workflow.add_edge("schema_retriever", "sql_generator")
        workflow.add_edge("sql_generator", "sql_validator")

        # Conditional routing after SQL validation (retry loop)
        workflow.add_conditional_edges(
            "sql_validator",
            route_after_validation,
            {
                "sql_executor": "sql_executor",
                "sql_generator": "sql_generator",
                "response_generator": "response_generator"
            }
        )

        # sql_executor -> conditional: retry with Claude on empty fine-tuned result, else context_enricher
        workflow.add_conditional_edges(
            "sql_executor",
            route_after_executor,
            {"sql_generator": "sql_generator", "context_enricher": "context_enricher"}
        )

        # Conditional routing after context enrichment
        workflow.add_conditional_edges(
            "context_enricher",
            route_after_execution,
            {
                "external_data_fetcher_hybrid": "external_data_fetcher_hybrid",
                "response_generator": "response_generator"
            }
        )

        # Hybrid path: external_data_fetcher -> response_generator
        workflow.add_edge("external_data_fetcher_hybrid", "response_generator")

        # Final edge
        workflow.add_edge("response_generator", END)

    return workflow.compile()


# Compile the graph
alpha_ai_graph = build_alpha_ai_graph()
