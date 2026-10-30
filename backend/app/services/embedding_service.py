import logging
import os
from typing import List, Optional

logger = logging.getLogger("carboniq.rag.embedding")

# Ensure huggingface doesn't hang retrying network requests when offline
if "HF_HUB_OFFLINE" not in os.environ:
    os.environ["HF_HUB_OFFLINE"] = "1"
if "TRANSFORMERS_OFFLINE" not in os.environ:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


class EmbeddingService:
    """
    Singleton service managing the Sentence Transformers embedding model.
    Guarantees:
    - Model is loaded once into memory and reused across all requests.
    - Embeddings are computed locally without third-party LLM API calls.
    - Vector dimension is fixed to 384 for 'sentence-transformers/all-MiniLM-L6-v2'.
    """

    _model: Optional[object] = None
    _model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    _dimension: int = 384

    @classmethod
    def get_dimension(cls) -> int:
        return cls._dimension

    @classmethod
    def get_model(cls) -> object:
        if cls._model is None:
            # Enforce offline flags before loading
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading cached SentenceTransformer model: {cls._model_name}...")
            cls._model = SentenceTransformer(cls._model_name)
            logger.info("SentenceTransformer model successfully initialized.")
        return cls._model

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        """Generates a 384-dimensional vector embedding for a single text query."""
        if not text or not text.strip():
            return [0.0] * cls._dimension
        model: any = cls.get_model()
        vec = model.encode(text.strip(), convert_to_numpy=True)
        return vec.tolist()

    @classmethod
    def embed_batch(cls, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text chunks efficiently."""
        if not texts:
            return []
        cleaned = [t.strip() if t and t.strip() else "" for t in texts]
        model: any = cls.get_model()
        vecs = model.encode(cleaned, batch_size=32, convert_to_numpy=True)
        return [v.tolist() for v in vecs]

