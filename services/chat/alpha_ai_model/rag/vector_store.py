# services/chat/alpha_ai_model/rag/vector_store.py
"""
Vector Store for Alpha AI

Manages vector embeddings for schema documents and few-shot examples.
Uses OpenAI embeddings and ChromaDB for similarity search.
"""
from typing import List, Dict, Any, Optional
from config import logger
import os

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("[VectorStore] ChromaDB not installed. Run: pip install chromadb")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("[VectorStore] OpenAI not installed. Run: pip install openai")


class VectorStore:
    """
    Vector Store for RAG

    Stores and retrieves document embeddings for similarity search.
    Uses ChromaDB for vector storage and OpenAI for embeddings.
    """

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        collection_name: str = "alpha_ai_schema",
        persist_directory: str = "./chroma_db"
    ):
        """
        Initialize VectorStore

        Args:
            embedding_model: OpenAI embedding model name
            collection_name: ChromaDB collection name
            persist_directory: Directory for persistent storage
        """
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.openai_client = None
        self.initialized = False

        logger.info(f"[VectorStore] Initialized with model: {embedding_model}")

    async def initialize(self) -> bool:
        """
        Initialize vector database connection

        Returns:
            True if successful, False otherwise
        """
        if not CHROMADB_AVAILABLE:
            logger.error("[VectorStore] ChromaDB not available")
            return False

        if not OPENAI_AVAILABLE:
            logger.error("[VectorStore] OpenAI not available")
            return False

        try:
            # Initialize OpenAI client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("[VectorStore] OPENAI_API_KEY not set")
                return False

            self.openai_client = OpenAI(api_key=api_key)

            # Initialize ChromaDB client
            chroma_host = os.getenv("CHROMA_HOST")
            if chroma_host:
                # Server mode (Railway deployment)
                chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
                chroma_ssl = os.getenv("CHROMA_SSL", "").lower() in ("true", "1", "yes")
                self.client = chromadb.HttpClient(
                    host=chroma_host,
                    port=chroma_port,
                    ssl=chroma_ssl
                )
                logger.info(f"[VectorStore] Using ChromaDB server: {chroma_host}:{chroma_port}")
            else:
                # Local mode (development)
                self.client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"[VectorStore] Using local ChromaDB: {self.persist_directory}")

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            self.initialized = True
            logger.info(f"[VectorStore] Initialized successfully. Collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"[VectorStore] Initialization failed: {e}")
            return False

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using OpenAI

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding

    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")

        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        return [item.embedding for item in response.data]

    def _build_where_clause(self, filter_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a ChromaDB-compatible where clause from filter metadata.

        ChromaDB requires compound filters (2+ keys) to use $and/$or operators.
        Single-key filters and existing $and/$or filters pass through unchanged.

        Args:
            filter_metadata: Raw filter dictionary

        Returns:
            ChromaDB-compatible where clause
        """
        if not filter_metadata:
            return filter_metadata

        # Already a compound operator ($and / $or) at top level
        if any(key.startswith("$") for key in filter_metadata):
            return filter_metadata

        # Single key - pass through as-is
        if len(filter_metadata) <= 1:
            return filter_metadata

        # Multiple keys - wrap in $and
        return {"$and": [{k: v} for k, v in filter_metadata.items()]}

    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        doc_type: str = "schema"
    ) -> int:
        """
        Add documents to vector store

        Args:
            documents: List of documents with 'content' and 'metadata'
            doc_type: Document type (schema, few_shot, term_mapping)

        Returns:
            Number of documents added
        """
        if not self.initialized:
            await self.initialize()

        if not self.collection:
            logger.error("[VectorStore] Collection not initialized")
            return 0

        try:
            # Prepare documents
            ids = []
            texts = []
            metadatas = []

            for i, doc in enumerate(documents):
                doc_id = f"{doc_type}_{i}_{hash(doc['content']) % 100000}"
                ids.append(doc_id)
                texts.append(doc["content"])

                metadata = doc.get("metadata", {})
                metadata["doc_type"] = doc_type
                metadatas.append(metadata)

            # Get embeddings in batches
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self._get_embeddings_batch(batch_texts)
                all_embeddings.extend(batch_embeddings)

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=all_embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"[VectorStore] Added {len(documents)} documents (type: {doc_type})")
            return len(documents)

        except Exception as e:
            logger.error(f"[VectorStore] Error adding documents: {e}")
            return 0

    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents

        Args:
            query: Search query
            top_k: Number of results
            filter_metadata: Optional metadata filters

        Returns:
            List of similar documents with scores
        """
        if not self.initialized:
            await self.initialize()

        if not self.collection:
            logger.warning("[VectorStore] Collection not initialized")
            return []

        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)

            # Build where clause for filtering
            where_clause = None
            if filter_metadata:
                where_clause = self._build_where_clause(filter_metadata)

            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )

            # Format results
            formatted_results = []
            if results and results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    # Convert distance to similarity score (cosine distance to similarity)
                    distance = results["distances"][0][i] if results["distances"] else 0
                    similarity = 1 - distance  # Cosine similarity

                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "score": similarity,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                    })

            logger.info(f"[VectorStore] Found {len(formatted_results)} results for query")
            return formatted_results

        except Exception as e:
            logger.error(f"[VectorStore] Search error: {e}")
            return []

    async def keyword_search(
        self,
        keywords: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Keyword-based search in documents

        Args:
            keywords: List of keywords to search
            top_k: Maximum number of results

        Returns:
            List of matching documents
        """
        if not self.initialized or not self.collection:
            return []

        try:
            # Get all documents and filter by keywords
            all_docs = self.collection.get(
                include=["documents", "metadatas"]
            )

            if not all_docs or not all_docs["documents"]:
                return []

            # Score documents by keyword matches
            scored_docs = []
            for i, doc in enumerate(all_docs["documents"]):
                doc_lower = doc.lower()
                score = sum(1 for kw in keywords if kw.lower() in doc_lower)

                if score > 0:
                    scored_docs.append({
                        "content": doc,
                        "score": score / len(keywords),  # Normalize
                        "metadata": all_docs["metadatas"][i] if all_docs["metadatas"] else {}
                    })

            # Sort by score and return top_k
            scored_docs.sort(key=lambda x: x["score"], reverse=True)
            return scored_docs[:top_k]

        except Exception as e:
            logger.error(f"[VectorStore] Keyword search error: {e}")
            return []

    async def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        top_k: int = 5,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector and keyword search with RRF

        Args:
            query: Search query for vector search
            keywords: Keywords for keyword search
            top_k: Number of results
            vector_weight: Weight for vector results (0-1)

        Returns:
            Combined and reranked results using RRF
        """
        # Get vector search results
        vector_results = await self.similarity_search(query, top_k * 2)

        # Get keyword search results
        keyword_results = await self.keyword_search(keywords, top_k * 2)

        # Apply Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        k = 60  # RRF constant

        # Score from vector results
        for rank, result in enumerate(vector_results):
            doc_key = result["content"][:100]  # Use first 100 chars as key
            if doc_key not in rrf_scores:
                rrf_scores[doc_key] = {"result": result, "score": 0}
            rrf_scores[doc_key]["score"] += vector_weight * (1 / (k + rank + 1))

        # Score from keyword results
        keyword_weight = 1 - vector_weight
        for rank, result in enumerate(keyword_results):
            doc_key = result["content"][:100]
            if doc_key in rrf_scores:
                rrf_scores[doc_key]["score"] += keyword_weight * (1 / (k + rank + 1))
            else:
                rrf_scores[doc_key] = {
                    "result": result,
                    "score": keyword_weight * (1 / (k + rank + 1))
                }

        # Sort by RRF score and return top_k
        sorted_results = sorted(
            rrf_scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        final_results = []
        for item in sorted_results[:top_k]:
            result = item["result"]
            result["rrf_score"] = item["score"]
            final_results.append(result)

        logger.info(f"[VectorStore] Hybrid search returned {len(final_results)} results")
        return final_results

    async def delete_by_type(self, doc_type: str) -> int:
        """
        Delete all documents of a specific type

        Args:
            doc_type: Document type to delete

        Returns:
            Number of documents deleted
        """
        if not self.initialized or not self.collection:
            return 0

        try:
            # Get documents of this type
            results = self.collection.get(
                where={"doc_type": doc_type},
                include=["metadatas"]
            )

            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"[VectorStore] Deleted {len(results['ids'])} documents of type: {doc_type}")
                return len(results["ids"])

            return 0

        except Exception as e:
            logger.error(f"[VectorStore] Delete error: {e}")
            return 0

    async def delete_collection(self) -> bool:
        """
        Delete the entire collection

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.client.delete_collection(self.collection_name)
            self.collection = None
            logger.info(f"[VectorStore] Deleted collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"[VectorStore] Delete collection error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get vector store statistics

        Returns:
            Statistics dictionary
        """
        stats = {
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model,
            "initialized": self.initialized,
            "document_count": 0,
            "persist_directory": self.persist_directory
        }

        if self.collection:
            try:
                stats["document_count"] = self.collection.count()
            except Exception:
                pass

        return stats
