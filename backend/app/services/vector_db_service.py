import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.core.config import settings
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger("carboniq.rag.qdrant")


class VectorDbService:
    """
    Manages connections, collections, and queries to the Qdrant Vector Database.
    Supports:
    Uses the configured remote Qdrant endpoint when set, and local persistent
    storage only when no remote endpoint is configured.
    """

    _client: Optional[QdrantClient] = None
    _collection_initialized: bool = False
    _is_available: bool = False
    _init_error: Optional[str] = None
    _active_mode: str = "uninitialized"

    @classmethod
    def sanitize_error(cls, error: Exception) -> str:
        message = str(error) or error.__class__.__name__
        for secret in (settings.QDRANT_API_KEY, settings.QDRANT_URL):
            if secret:
                message = message.replace(secret, "[redacted]")
        return message

    @classmethod
    def get_last_error(cls) -> Optional[str]:
        return cls._init_error

    @classmethod
    def resolve_storage_path(cls) -> Path:
        """Resolves local storage path relative to backend root."""
        p = Path(settings.QDRANT_STORAGE_PATH)
        if not p.is_absolute():
            backend_dir = Path(__file__).resolve().parents[2]
            p = backend_dir / settings.QDRANT_STORAGE_PATH
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_client(cls) -> Optional[QdrantClient]:
        """Returns the shared QdrantClient instance, creating it if needed."""
        if cls._client is not None:
            return cls._client

        # A configured cloud endpoint is authoritative; never silently use a
        # different local collection when that endpoint is unavailable.
        if settings.QDRANT_URL and settings.QDRANT_URL.strip():
            client: Optional[QdrantClient] = None
            try:
                import socket
                import urllib.parse

                raw_url = settings.QDRANT_URL.strip()
                parsed = urllib.parse.urlparse(raw_url)
                host = parsed.hostname
                if not host:
                    raise ValueError("QDRANT_URL does not contain a valid hostname.")
                port = parsed.port or (443 if parsed.scheme == "https" else 6333)

                with socket.create_connection((host, port), timeout=1.5):
                    pass

                logger.info("Connecting to configured remote Qdrant cluster.")
                client = QdrantClient(
                    url=raw_url,
                    api_key=settings.QDRANT_API_KEY.strip() if settings.QDRANT_API_KEY else None,
                    timeout=5.0,
                    check_compatibility=False,
                )
                client.get_collections()
                cls._client = client
                cls._is_available = True
                cls._active_mode = "remote_cluster"
                cls._init_error = None
                if not cls.ensure_collection():
                    cls._is_available = False
                    try:
                        client.close()
                    except Exception:
                        logger.debug("Unable to close invalid remote Qdrant client.")
                    cls._client = None
                    return None
                return cls._client
            except Exception as remote_err:
                cls._is_available = False
                cls._active_mode = "remote_cluster"
                cls._init_error = cls.sanitize_error(remote_err)
                if client is not None:
                    try:
                        client.close()
                    except Exception:
                        logger.debug("Unable to close failed remote Qdrant client.")
                logger.warning("Configured remote Qdrant connection failed: %s", cls._init_error)
                return None

        try:
            storage_path = cls.resolve_storage_path()
            logger.info(f"Using local persistent Qdrant storage at: {storage_path}")
            cls._client = QdrantClient(path=str(storage_path))
            cls._is_available = True
            cls._active_mode = "local_persistent"
            cls._init_error = None
            if not cls.ensure_collection():
                cls._is_available = False
                try:
                    cls._client.close()
                except Exception:
                    logger.debug("Unable to close invalid local Qdrant client.")
                cls._client = None
                return None
            return cls._client
        except Exception as local_err:
            cls._client = None
            cls._is_available = False
            cls._active_mode = "local_persistent"
            cls._init_error = cls.sanitize_error(local_err)
            logger.warning(
                "Could not initialize local Qdrant storage: %s. "
                "RAG features will gracefully report knowledge base unavailable.",
                cls._init_error,
            )
            return None

    @classmethod
    def is_available(cls) -> bool:
        """Checks if Qdrant client is initialized and reachable."""
        if cls._client is None:
            cls.get_client()
        return cls._is_available

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns diagnostic status of the vector database."""
        client = cls.get_client()
        available = client is not None and cls._is_available
        total_vectors = 0
        collection_exists = False
        vector_distance = None
        if available:
            try:
                info = client.get_collection(collection_name=settings.QDRANT_COLLECTION_NAME)
                collection_exists = True
                vectors = info.config.params.vectors
                if isinstance(vectors, models.VectorParams):
                    vector_distance = vectors.distance.value
                elif isinstance(vectors, dict):
                    default_vector = vectors.get("")
                    if default_vector is not None:
                        vector_distance = default_vector.distance.value
                count_info = client.count(collection_name=settings.QDRANT_COLLECTION_NAME)
                total_vectors = count_info.count
            except Exception as status_err:
                cls._init_error = cls.sanitize_error(status_err)

        mode = cls._active_mode if cls._active_mode != "uninitialized" else ("remote_cluster" if settings.QDRANT_URL else "local_persistent")
        return {
            "is_available": available,
            "mode": mode,
            "collection_name": settings.QDRANT_COLLECTION_NAME,
            "collection_exists": collection_exists,
            "total_vectors": total_vectors,
            "vector_dimension": EmbeddingService.get_dimension(),
            "vector_distance": vector_distance,
            "storage_path": str(cls.resolve_storage_path()) if mode == "local_persistent" else None,
            "qdrant_url": None,
            "init_error": cls._init_error,
        }

    @classmethod
    def ensure_collection(cls) -> bool:
        """Ensures the sustainability vector collection exists with cosine distance."""
        if cls._collection_initialized:
            return True

        if cls._client is None:
            return False

        collection_name = settings.QDRANT_COLLECTION_NAME
        dim = EmbeddingService.get_dimension()

        try:
            collections = cls._client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)

            if not exists:
                logger.info(f"Creating Qdrant collection '{collection_name}' with dimension {dim} (Cosine)...")
                cls._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
                )
                # Create payload indexes for efficient filtering
                try:
                    cls._client.create_payload_index(
                        collection_name=collection_name,
                        field_name="category",
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                    cls._client.create_payload_index(
                        collection_name=collection_name,
                        field_name="doc_id",
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )
                except Exception as idx_err:
                    logger.debug(f"Payload index creation note: {idx_err}")

            info = cls._client.get_collection(collection_name=collection_name)
            vectors = info.config.params.vectors
            if isinstance(vectors, models.VectorParams):
                vector_params = vectors
            elif isinstance(vectors, dict):
                vector_params = vectors.get("")
            else:
                vector_params = None
            if vector_params is None:
                raise ValueError("Qdrant collection does not have a default unnamed vector configuration.")
            if vector_params.size != dim or vector_params.distance != models.Distance.COSINE:
                raise ValueError(
                    f"Qdrant collection '{collection_name}' is configured for "
                    f"size={vector_params.size}, distance={vector_params.distance}; "
                    f"expected size={dim}, distance=Cosine."
                )

            cls._collection_initialized = True
            cls._init_error = None
            return True
        except Exception as e:
            cls._init_error = cls.sanitize_error(e)
            cls._is_available = False
            logger.error("Error ensuring Qdrant collection '%s': %s", collection_name, cls._init_error)
            cls._collection_initialized = False
            return False

    @classmethod
    def upsert_chunks(cls, chunks: List[Dict[str, Any]]) -> int:
        """
        Stores chunk vectors and metadata into Qdrant.
        Each chunk dictionary should have:
        - 'id': str or uuid (or auto-generated)
        - 'vector': List[float] (384-dimensional embedding)
        - 'payload': Dict containing 'text', 'title', 'source', 'category', 'doc_id', etc.
        """
        client = cls.get_client()
        if client is None or not chunks:
            return 0

        if not cls.ensure_collection():
            raise RuntimeError(cls.get_last_error() or "Qdrant collection is unavailable.")
        collection_name = settings.QDRANT_COLLECTION_NAME

        points = []
        for ch in chunks:
            vector = ch.get("vector")
            if not isinstance(vector, list) or len(vector) != EmbeddingService.get_dimension():
                raise ValueError(
                    f"Invalid embedding dimension: expected {EmbeddingService.get_dimension()} values."
                )
            point_id = ch.get("id")
            if not point_id:
                point_id = str(uuid.uuid4())
            elif isinstance(point_id, str):
                # Ensure valid UUID or integer for Qdrant PointStruct ID
                try:
                    point_id = str(uuid.UUID(point_id))
                except ValueError:
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, point_id))

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=ch["payload"],
                )
            )

        client.upsert(
            collection_name=collection_name,
            points=points,
            wait=True,
        )
        logger.info(f"Successfully upserted {len(points)} points into '{collection_name}'.")
        return len(points)

    @classmethod
    def search(
        cls,
        query_vector: List[float],
        category: Optional[str] = None,
        limit: int = 3,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search against indexed sustainability documents.
        Supports optional category filtering and score thresholding.
        """
        client = cls.get_client()
        if client is None:
            raise RuntimeError(cls.get_last_error() or "Qdrant is unavailable.")

        if len(query_vector) != EmbeddingService.get_dimension():
            raise ValueError(
                f"Invalid query embedding dimension: expected {EmbeddingService.get_dimension()}, "
                f"received {len(query_vector)}."
            )
        if not cls.ensure_collection():
            raise RuntimeError(cls.get_last_error() or "Qdrant collection is unavailable.")
        collection_name = settings.QDRANT_COLLECTION_NAME

        query_filter = None
        if category and category.strip():
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="category",
                        match=models.MatchValue(value=category.strip()),
                    )
                ]
            )

        threshold = score_threshold if score_threshold is not None else settings.RAG_SCORE_THRESHOLD

        try:
            res = client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=threshold,
                with_payload=True,
            )
        except Exception as search_error:
            cls._init_error = cls.sanitize_error(search_error)
            logger.error("Semantic search in Qdrant failed: %s", cls._init_error)
            raise

        results: List[Dict[str, Any]] = []
        for pt in res.points:
            payload = pt.payload or {}
            results.append(
                {
                    "chunk_id": str(pt.id),
                    "similarity_score": round(float(pt.score), 4),
                    "text": payload.get("text"),
                    "title": payload.get("title"),
                    "source": payload.get("source"),
                    "category": payload.get("category"),
                    "doc_id": payload.get("doc_id"),
                    "chunk_index": payload.get("chunk_index", 0),
                    "publication_date": payload.get("publication_date"),
                }
            )
        return results

    @classmethod
    def get_document_content_hash(cls, doc_id: str) -> Optional[str]:
        """Returns a document's indexed content hash without loading its vectors."""
        client = cls.get_client()
        if client is None or not cls.ensure_collection():
            return None
        points, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
            ),
            limit=1,
            with_payload=["content_hash"],
            with_vectors=False,
        )
        if not points or not points[0].payload:
            return None
        value = points[0].payload.get("content_hash")
        return str(value) if value else None

    @classmethod
    def delete_document(cls, doc_id: str) -> bool:
        """Deletes all indexed chunks for a given document identifier."""
        client = cls.get_client()
        if client is None:
            return False

        collection_name = settings.QDRANT_COLLECTION_NAME
        try:
            client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="doc_id",
                                match=models.MatchValue(value=doc_id),
                            )
                        ]
                    )
                ),
            )
            logger.info(f"Deleted indexed chunks for doc_id='{doc_id}' from '{collection_name}'.")
            return True
        except Exception as e:
            cls._init_error = cls.sanitize_error(e)
            logger.error("Failed to delete document chunks from Qdrant: %s", cls._init_error)
            return False

    @classmethod
    def close(cls) -> None:
        """Closes the Qdrant client connection pool."""
        if cls._client is not None:
            try:
                cls._client.close()
            except Exception:
                pass
            cls._client = None
            cls._collection_initialized = False
            cls._is_available = False
            logger.info("Closed Qdrant vector database connection.")