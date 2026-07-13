from dataclasses import dataclass
from typing import Protocol

from pinecone import Pinecone


@dataclass(frozen=True)
class VectorRecord:
    id: str
    values: list[float]
    metadata: dict


@dataclass(frozen=True)
class VectorMatch:
    id: str
    score: float


class VectorStore(Protocol):
    def upsert(self, records: list[VectorRecord]) -> None: ...
    def search(self, *, document_id: str, query_vector: list[float], top_k: int) -> list[VectorMatch]: ...
    def delete_document(self, document_id: str) -> None: ...
    def ready(self) -> bool: ...


class PineconeVectorStore:
    def __init__(self, api_key: str, index_name: str):
        self._api_key = api_key
        self._index_name = index_name
        self._index = None

    def _get_index(self):
        if self._index is None:
            self._index = Pinecone(api_key=self._api_key).Index(self._index_name)
        return self._index

    def upsert(self, records: list[VectorRecord]) -> None:
        self._get_index().upsert(vectors=[{"id": r.id, "values": r.values, "metadata": r.metadata} for r in records])

    def search(self, *, document_id: str, query_vector: list[float], top_k: int) -> list[VectorMatch]:
        result = self._get_index().query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=False,
            filter={"document_id": {"$eq": document_id}},
        )
        return [VectorMatch(id=m.id, score=float(m.score)) for m in result.matches]

    def delete_document(self, document_id: str) -> None:
        self._get_index().delete(filter={"document_id": {"$eq": document_id}})

    def ready(self) -> bool:
        try:
            self._get_index().describe_index_stats()
            return True
        except Exception:
            return False


class UnconfiguredVectorStore:
    def _fail(self):
        raise RuntimeError("Vector store is not configured")

    def upsert(self, records: list[VectorRecord]) -> None:
        self._fail()

    def search(self, *, document_id: str, query_vector: list[float], top_k: int) -> list[VectorMatch]:
        self._fail()

    def delete_document(self, document_id: str) -> None:
        self._fail()

    def ready(self) -> bool:
        return False
