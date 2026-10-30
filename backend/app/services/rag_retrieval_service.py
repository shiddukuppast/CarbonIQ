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
        limit = top_k if top_k is not None else settings.RAG_TOP_K

        # If vector database is not reachable, gracefully report limitation
        if not VectorDbService.is_available():
            connection_error = VectorDbService.get_last_error()
            return {
                "has_knowledge": False,
                "chunks": [],
                "sources": [],
                "retrieval_status": "unavailable",
                "knowledge_limitation": (
                    f"Qdrant is unavailable: {connection_error}"
                    if connection_error
                    else "Qdrant is unavailable or not initialized."
                ),
                "search_count": 0,
            }

        if not clean_q or len(clean_q) < 3:
            return {
                "has_knowledge": False,
                "chunks": [],
                "sources": [],
                "retrieval_status": "no_support",
                "knowledge_limitation": "Query was too short to perform semantic knowledge retrieval.",
                "search_count": 0,
            }

        try:
            # 1. Convert question to vector embedding using Sentence Transformers
            query_vector = EmbeddingService.embed_text(clean_q)
            if len(query_vector) != EmbeddingService.get_dimension():
                raise ValueError(
                    f"Query embedding has {len(query_vector)} dimensions; expected "
                    f"{EmbeddingService.get_dimension()}."
                )

            # 2. Query Qdrant for semantic similarity
            results = VectorDbService.search(
                query_vector=query_vector,
                category=category,
                limit=limit,
                score_threshold=score_threshold,
            )

            # A point without its indexed text and source metadata cannot support
            # an answer or be cited.
            match_count = len(results)
            results = [
                item for item in results
                if isinstance(item.get("text"), str)
                and item["text"].strip()
                and isinstance(item.get("title"), str)
                and item["title"].strip()
                and isinstance(item.get("source"), str)
                and item["source"].strip()
            ]
            if not results:
                return {
                    "has_knowledge": False,
                    "chunks": [],
                    "sources": [],
                    "retrieval_status": "invalid_payload" if match_count else "no_support",
                    "knowledge_limitation": (
                        "Qdrant returned matches without document text or source metadata."
                        if match_count
                        else "No supporting sustainability documents matched this question."
                    ),
                    "search_count": 0,
                }

            # 3. Format sources and extract key snippets
            formatted_sources: List[str] = []
            seen_sources = set()

            for item in results:
                src_key = f"{item['title']} ({item['source']})"
                if src_key not in seen_sources:
                    seen_sources.add(src_key)
                    formatted_sources.append(src_key)

            return {
                "has_knowledge": True,
                "chunks": results,
                "sources": formatted_sources,
                "retrieval_status": "retrieved",
                "knowledge_limitation": None,
                "search_count": len(results),
            }

        except Exception as e:
            logger.error(
                "Error during RAG knowledge retrieval: %s",
                VectorDbService.sanitize_error(e),
            )
            return {
                "has_knowledge": False,
                "chunks": [],
                "sources": [],
                "retrieval_status": "error",
                "knowledge_limitation": f"Knowledge retrieval failed: {VectorDbService.sanitize_error(e)}",
                "search_count": 0,
            }
