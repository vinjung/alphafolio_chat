# services/chat/alpha_ai_model/graph/nodes/__init__.py
"""
Alpha AI LangGraph Nodes

Each node handles a specific step in the Text-to-SQL pipeline.
Phase 5 adds external data and hybrid analysis nodes.
"""
from .intent_classifier import intent_classifier
from .entity_extractor import entity_extractor
from .schema_retriever import schema_retriever
from .sql_generator import sql_generator
from .sql_validator import sql_validator
from .sql_executor import sql_executor
from .response_generator import response_generator

# Phase 5: External Data & Hybrid Analysis
from .data_source_router import data_source_router
from .external_data_fetcher import external_data_fetcher
# Phase 6: Context Enrichment
from .context_enricher import context_enricher

# Unified Classifier (feature flag: USE_UNIFIED_CLASSIFIER)
from .unified_classifier import unified_classifier

# Query Decomposition (feature flag: USE_QUERY_DECOMPOSITION)
from .query_decomposer import query_decomposer
from .parallel_sql_pipeline import parallel_sql_pipeline

# Query Router - hybrid simple/complex routing (feature flag: USE_QUERY_DECOMPOSITION)
from .query_router import query_router

__all__ = [
    # Core pipeline
    "intent_classifier",
    "entity_extractor",
    "schema_retriever",
    "sql_generator",
    "sql_validator",
    "sql_executor",
    "response_generator",
    # Phase 5: External data
    "data_source_router",
    "external_data_fetcher",
    # Phase 6: Context enrichment
    "context_enricher",
    # Unified Classifier
    "unified_classifier",
    # Query Decomposition
    "query_decomposer",
    "parallel_sql_pipeline",
    # Query Router
    "query_router",
]
