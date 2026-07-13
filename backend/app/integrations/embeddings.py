from functools import lru_cache
from typing import Protocol

from sentence_transformers import SentenceTransformer


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str):
        self.model_name = model_name

    @lru_cache(maxsize=1)
    def _model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._model().encode(texts, normalize_embeddings=True).tolist()
