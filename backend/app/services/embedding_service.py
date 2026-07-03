"""Sentence-Transformers embedding singleton (DDD Stage 3).

The SAME singleton instance is used by both the resume pipeline and the course
embedding pipeline, guaranteeing identical vector spaces.

Model: all-MiniLM-L6-v2 (384-dim). Loaded once, lazily, via @lru_cache.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 32
EMBEDDING_DIM = 384


class EmbeddingService:
    """Thin wrapper around a SentenceTransformer model."""

    def __init__(self, model_name: str) -> None:
        # Imported lazily so the heavy dependency is only loaded when needed.
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model '%s' ...", model_name)
        self._model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info("Embedding model loaded.")

    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode a list of texts into L2-normalized 384-dim vectors.

        Returns a numpy array of shape (len(texts), 384). Call `.tolist()` for
        ChromaDB. Uses the model default L2 normalization.
        """
        if not texts:
            return np.empty((0, EMBEDDING_DIM), dtype="float32")
        return self._model.encode(
            texts,
            batch_size=BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def encode_one(self, text: str) -> List[float]:
        """Encode a single string, returning a plain python list."""
        return self.encode([text])[0].tolist()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Return the cached embedding service singleton."""
    settings = get_settings()
    return EmbeddingService(settings.embedding_model_name)
