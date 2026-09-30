"""Embedding generator using sentence-transformers."""

import os
from typing import List, Optional, Union

import numpy as np


class EmbeddingServiceError(Exception):
    pass


class EmbeddingService:
    """Generate dense embeddings for documents and queries."""

    def __init__(self, model_name: Optional[str] = None, cache_dir: Optional[str] = None):
        self.model_name = model_name or os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.cache_dir = cache_dir or os.environ.get('TRANSFORMERS_CACHE', 'models')
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, cache_folder=self.cache_dir)
            except ImportError as exc:
                raise EmbeddingServiceError(
                    'sentence-transformers is not installed. Run: pip install sentence-transformers'
                ) from exc
            except Exception as exc:
                raise EmbeddingServiceError(f'Failed to load embedding model: {exc}') from exc
        return self._model

    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        """Encode text(s) into embeddings."""
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            raise EmbeddingServiceError('Cannot encode empty text list.')

        model = self._load_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            embeddings = embeddings / norms

        return embeddings

    def encode_single(self, text: str) -> List[float]:
        """Encode a single text and return as a Python list."""
        embeddings = self.encode([text])
        return embeddings[0].tolist()


embedding_service = EmbeddingService()
