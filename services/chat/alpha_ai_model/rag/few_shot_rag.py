# services/chat/alpha_ai_model/rag/few_shot_rag.py
"""
Few-Shot RAG for Alpha AI

Retrieves relevant SQL examples based on user query similarity.
Uses vector search to find the most similar question-SQL pairs.
"""
from typing import List, Dict, Any, Optional
from config import logger

from .vector_store import VectorStore
from ..prompts.few_shot_examples import FEW_SHOT_EXAMPLES


class FewShotRAG:
    """
    Few-Shot Retrieval-Augmented Generation

    Retrieves relevant SQL examples for in-context learning.
    Indexes question-SQL pairs and retrieves based on semantic similarity.
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize FewShotRAG

        Args:
            vector_store: Vector store instance for similarity search
        """
        self.vector_store = vector_store or VectorStore(
            collection_name="alpha_ai_few_shot"
        )
        self.initialized = False
        logger.info("[FewShotRAG] Initialized")

    async def initialize(self) -> bool:
        """
        Initialize vector store with few-shot examples

        Returns:
            True if successful
        """
        if self.initialized:
            return True

        try:
            # Initialize vector store
            success = await self.vector_store.initialize()
            if not success:
                logger.error("[FewShotRAG] Vector store initialization failed")
                return False

            # Check if examples are already indexed
            stats = await self.vector_store.get_stats()
            if stats.get("document_count", 0) > 0:
                logger.info("[FewShotRAG] Examples already indexed")
                self.initialized = True
                return True

            # Index few-shot examples
            await self._index_examples()

            self.initialized = True
            logger.info("[FewShotRAG] Initialization complete")
            return True

        except Exception as e:
            logger.error(f"[FewShotRAG] Initialization failed: {e}")
            return False

    async def _index_examples(self) -> None:
        """
        Index all few-shot examples into vector store
        """
        logger.info("[FewShotRAG] Indexing few-shot examples...")

        documents = []

        for example in FEW_SHOT_EXAMPLES:
            # Create document content (question + SQL for embedding)
            content = f"Question: {example['question']}\nSQL: {example['sql']}"

            # Extract metadata
            metadata = {
                "question": example["question"],
                "sql": example["sql"],
                "category": example.get("category", "query"),
                "market": example.get("market", "KR"),
                "complexity": self._assess_complexity(example["sql"]),
                "tables_used": self._extract_tables(example["sql"]),
                "chart_indicators": example.get("chart_indicators", False)
            }

            documents.append({
                "content": content,
                "metadata": metadata
            })

        # Add to vector store
        count = await self.vector_store.add_documents(documents, doc_type="few_shot")
        logger.info(f"[FewShotRAG] Indexed {count} few-shot examples")

    def _assess_complexity(self, sql: str) -> str:
        """
        Assess SQL complexity

        Args:
            sql: SQL query

        Returns:
            Complexity level (simple, medium, complex)
        """
        sql_upper = sql.upper()

        # Count complexity indicators
        indicators = 0

        if "JOIN" in sql_upper:
            indicators += 1
        if "SUBQUERY" in sql_upper or sql_upper.count("SELECT") > 1:
            indicators += 2
        if "GROUP BY" in sql_upper:
            indicators += 1
        if "HAVING" in sql_upper:
            indicators += 1
        if "CASE" in sql_upper:
            indicators += 1
        if "WITH" in sql_upper:
            indicators += 2
        if sql_upper.count("AND") + sql_upper.count("OR") > 2:
            indicators += 1

        if indicators == 0:
            return "simple"
        elif indicators <= 2:
            return "medium"
        else:
            return "complex"

    def _extract_tables(self, sql: str) -> str:
        """
        Extract table names from SQL

        Args:
            sql: SQL query

        Returns:
            Comma-separated table names
        """
        import re

        # Find tables after FROM and JOIN
        tables = set()

        # FROM clause
        from_match = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        tables.update(from_match)

        # JOIN clause
        join_match = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.update(join_match)

        return ",".join(sorted(tables))

    async def retrieve_examples(
        self,
        query: str,
        intent: str = None,
        market: str = "KR",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant few-shot examples

        Args:
            query: User query
            intent: Query intent (optional filter)
            market: Market filter (KR/US)
            top_k: Number of examples to retrieve

        Returns:
            List of relevant examples
        """
        if not self.initialized:
            await self.initialize()

        logger.info(f"[FewShotRAG] Retrieving examples for: {query[:50]}...")

        # Build metadata filter (BOTH -> union of KR/US/BOTH)
        if market == "BOTH":
            market_filter = {"$or": [{"market": "KR"}, {"market": "US"}, {"market": "BOTH"}]}
        else:
            market_filter = {"market": market}

        if intent:
            if market == "BOTH":
                filter_metadata = {"$and": [{"category": intent}, market_filter]}
            else:
                filter_metadata = {"market": market, "category": intent}
        else:
            filter_metadata = market_filter

        # Search for similar examples
        results = await self.vector_store.similarity_search(
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        # If no results with filter, try without intent filter
        if not results and intent:
            results = await self.vector_store.similarity_search(
                query=query,
                top_k=top_k,
                filter_metadata=market_filter
            )

        # Format results
        examples = []
        for result in results:
            metadata = result.get("metadata", {})
            examples.append({
                "question": metadata.get("question", ""),
                "sql": metadata.get("sql", ""),
                "category": metadata.get("category", "query"),
                "market": metadata.get("market", "KR"),
                "complexity": metadata.get("complexity", "simple"),
                "relevance": result.get("score", 0),
                "chart_indicators": metadata.get("chart_indicators", False)
            })

        logger.info(f"[FewShotRAG] Found {len(examples)} relevant examples")
        return examples

    async def retrieve_by_category(
        self,
        category: str,
        market: str = "KR",
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve examples by category

        Args:
            category: Example category (ranking, filter, technical, etc.)
            market: Market filter
            top_k: Number of examples

        Returns:
            List of examples
        """
        if not self.initialized:
            await self.initialize()

        # Filter by category (BOTH -> union of KR/US/BOTH)
        if market == "BOTH":
            filter_metadata = {"$and": [
                {"category": category},
                {"$or": [{"market": "KR"}, {"market": "US"}, {"market": "BOTH"}]}
            ]}
        else:
            filter_metadata = {
                "category": category,
                "market": market
            }

        # Use a generic query for category-based retrieval
        category_queries = {
            "ranking": "Top N stocks by criteria",
            "filter": "Filter stocks by condition",
            "technical": "Technical indicator analysis",
            "investor": "Investor trading flow",
            "quant": "Quant grade analysis",
            "market": "Market index query",
            "query": "Stock information lookup"
        }

        query = category_queries.get(category, "Stock data query")

        results = await self.vector_store.similarity_search(
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )

        examples = []
        for result in results:
            metadata = result.get("metadata", {})
            examples.append({
                "question": metadata.get("question", ""),
                "sql": metadata.get("sql", ""),
                "category": metadata.get("category", "query"),
                "market": metadata.get("market", "KR")
            })

        return examples

    async def hybrid_retrieve(
        self,
        query: str,
        intent: str = None,
        market: str = "KR",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining vector search and keyword matching

        Args:
            query: User query
            intent: Query intent
            market: Market filter
            top_k: Number of examples

        Returns:
            Combined and reranked examples
        """
        if not self.initialized:
            await self.initialize()

        # Extract keywords from query
        keywords = self._extract_keywords(query)

        # Hybrid search
        results = await self.vector_store.hybrid_search(
            query=query,
            keywords=keywords,
            top_k=top_k,
            vector_weight=0.7
        )

        # Filter by market (BOTH -> accept KR/US/BOTH/COMMON)
        examples = []
        for result in results:
            metadata = result.get("metadata", {})
            result_market = metadata.get("market")
            if market == "BOTH":
                market_match = result_market in ("KR", "US", "BOTH", "COMMON")
            else:
                market_match = result_market == market or result_market == "COMMON"
            if market_match:
                examples.append({
                    "question": metadata.get("question", ""),
                    "sql": metadata.get("sql", ""),
                    "category": metadata.get("category", "query"),
                    "market": metadata.get("market", "KR"),
                    "relevance": result.get("rrf_score", result.get("score", 0)),
                    "chart_indicators": metadata.get("chart_indicators", False)
                })

        return examples[:top_k]

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from query for keyword search

        Args:
            query: User query

        Returns:
            List of keywords
        """
        # Common SQL-related keywords
        keyword_patterns = [
            "거래대금", "거래량", "시총", "시가총액",
            "상위", "top", "랭킹", "순위",
            "rsi", "macd", "볼린저", "이평",
            "외국인", "기관", "개인",
            "등급", "점수", "grade", "score",
            "코스피", "코스닥", "나스닥",
            "과매수", "과매도", "골든크로스"
        ]

        query_lower = query.lower()
        found_keywords = []

        for kw in keyword_patterns:
            if kw.lower() in query_lower:
                found_keywords.append(kw)

        return found_keywords

    def format_for_prompt(self, examples: List[Dict[str, Any]]) -> str:
        """
        Format examples for inclusion in SQL generation prompt

        Args:
            examples: List of example dictionaries

        Returns:
            Formatted string for prompt
        """
        if not examples:
            return "No similar examples found."

        lines = ["## Similar Examples"]

        for i, example in enumerate(examples, 1):
            lines.append(f"\n### Example {i}")
            lines.append(f"Question: {example['question']}")
            lines.append(f"```sql\n{example['sql']}\n```")

        return "\n".join(lines)

    async def reindex(self) -> bool:
        """
        Reindex all few-shot examples

        Returns:
            True if successful
        """
        try:
            # Delete existing examples
            await self.vector_store.delete_by_type("few_shot")

            # Reindex
            await self._index_examples()

            logger.info("[FewShotRAG] Reindex complete")
            return True

        except Exception as e:
            logger.error(f"[FewShotRAG] Reindex failed: {e}")
            return False

    async def add_example(
        self,
        question: str,
        sql: str,
        category: str = "query",
        market: str = "KR"
    ) -> bool:
        """
        Add a new example to the index

        Args:
            question: Example question
            sql: Example SQL
            category: Query category
            market: Market (KR/US)

        Returns:
            True if successful
        """
        if not self.initialized:
            await self.initialize()

        try:
            content = f"Question: {question}\nSQL: {sql}"

            document = {
                "content": content,
                "metadata": {
                    "question": question,
                    "sql": sql,
                    "category": category,
                    "market": market,
                    "complexity": self._assess_complexity(sql),
                    "tables_used": self._extract_tables(sql)
                }
            }

            count = await self.vector_store.add_documents([document], doc_type="few_shot")
            logger.info(f"[FewShotRAG] Added new example: {question[:50]}...")
            return count > 0

        except Exception as e:
            logger.error(f"[FewShotRAG] Failed to add example: {e}")
            return False
