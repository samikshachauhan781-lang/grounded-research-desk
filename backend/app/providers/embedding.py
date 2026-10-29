"""Embedding provider interfaces and implementations."""

from abc import ABC, abstractmethod
import hashlib
import re

import numpy as np

from backend.app.core.config import Settings
from backend.app.core.exceptions import EmbeddingError


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[np.ndarray]:
        raise NotImplementedError


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic bag-of-words style vectors for offline tests."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = settings.embedding_model_name
        self._dim = settings.embedding_dimension

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dim

    def _embed_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self._dim, dtype=np.float32)
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode()).hexdigest()
            idx = int(digest[:8], 16) % self._dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm == 0.0:
            vec[0] = 1.0
        else:
            vec /= norm
        return vec

    def embed_texts(self, texts: list[str]) -> list[np.ndarray]:
        return [self._embed_one(text) for text in texts]


class LocalSentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, settings: Settings) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError(
                "sentence-transformers not installed. pip install '.[local]'",
            ) from exc
        self._settings = settings
        model_id = settings.embedding_model_name
        if not model_id.startswith("sentence-transformers/"):
            model_id = f"sentence-transformers/{model_id}"
        self._model_name = model_id
        self._model = SentenceTransformer(model_id, device=settings.embedding_device)
        dim = self._model.get_sentence_embedding_dimension()
        if dim != settings.embedding_dimension:
            raise EmbeddingError(
                f"Model dimension {dim} != configured EMBEDDING_DIMENSION",
            )

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._settings.embedding_dimension

    def embed_texts(self, texts: list[str]) -> list[np.ndarray]:
        vectors = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return [np.asarray(v, dtype=np.float32) for v in vectors]


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "local":
        return LocalSentenceTransformerProvider(settings)
    return FakeEmbeddingProvider(settings)
