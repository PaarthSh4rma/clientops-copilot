from functools import lru_cache
from typing import Protocol

from pinecone import Pinecone


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str):
        self.model_name = model_name

    @lru_cache(maxsize=1)
    def _model(self):
        # Keep the heavyweight local model optional for serverless deployments.
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._model().encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]


class PineconeInferenceEmbeddings:
    def __init__(self, api_key: str, model_name: str):
        self._client = Pinecone(api_key=api_key)
        self.model_name = model_name

    def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        if not texts:
            return []
        result = self._client.inference.embed(
            model=self.model_name,
            inputs=texts,
            parameters={"input_type": input_type, "truncate": "END"},
        )
        return [list(item.values) for item in result]

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "passage")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "query")[0]
