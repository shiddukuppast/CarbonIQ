import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_db_service import VectorDbService

logger = logging.getLogger("carboniq.rag.retrieval")


class RagRetrievalService:
    """
    Retrieval-Augmented Generation (RAG) Service for CarbonIQ.
    Retrieves grounded, high-similarity external sustainability reference chunks
    from the Qdrant vector database.
    Guarantees:
    - Never fabricates documents or citations.
    - Applies category filtering when querying within specialized domain advisors.
    - Limits retrieval count to a compact, top-k window to minimize LLM token usage and latency.
    - Explicitly reports knowledge limitations when no relevant chunks match.
    """

    @classmethod
    async def retrieve_relevant_knowledge(
        cls,
        query: str,
        category: Optional[str] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Executes semantic retrieval for a user sustainability question.
        Returns structured dictionary containing retrieved chunks, supporting source strings,
        and explicit knowledge limitation notes if matching documentation is unavailable.
        """
        clean_q = (query or "").strip()
        limit = top_k or settings.RAG_TOP_K

        # If vector database is not reachable, gracefully report limitation
        if not VectorDbService.is_available():
            return {
                "has_knowledge": False,
                "chunks": [],
                "sources": [],
                "knowledge_limitation": "External vector knowledge base is currently offline or uninitialized.",
                "search_count": 0,
            }

        if not clean_q or len(clean_q) < 3:
            return {
                "has_knowledge": False,
                "chunks": [],
                "sources": [],
                "knowledge_limitation": "Query was too short to perform semantic knowledge retrieval.",
                "search_count": 0,
            }

        try:
            # 1. Convert question to vector embedding using Sentence Transformers
            query_vector = EmbeddingService.embed_text(clean_q)

            # 2. Query Qdrant for semantic similarity
            results = VectorDbService.search(
                query_vector=query_vector,
                category=category,
                limit=limit,
                score_threshold=score_threshold,
            )

            if not results:
                return {
                    "has_knowledge": False,
                    "chunks": [],
                    "sources": [],
                    "knowledge_limitation": f"No high-confidence sustainability reference documents matched the inquiry '{clean_q[:60]}...'.",
                    "search_count": 0,
                }

            # 3. Format sources and extract key snippets
            formatted_sources: List[str] = []
            seen_sources = set()

            for item in results:
                title = item.get("title") or "Sustainability Standard"
                src = item.get("source") or "CarbonIQ Knowledge Base"
                src_key = f"{title} ({src})"
                if src_key not in seen_sources:
                    seen_sources.add(src_key)
                    formatted_sources.append(src_key)

            return {
                "has_knowledge": True,
                "chunks": results,
                "sources": formatted_sources,
                "knowledge_limitation": None,
                "search_count": len(results),
            }

        except Exception as e:
            logger.error(f"Error during RAG knowledge retrieval: {e}")
            return {
                "has_knowledge": False,
                "chunks": [],
                "sources": [],
                "knowledge_limitation": "External sustainability retrieval encountered a temporary system error.",
                "search_count": 0,
            }

