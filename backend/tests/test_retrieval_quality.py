from math import sqrt

from app.integrations.vector_store import VectorMatch, VectorRecord
from app.models import Document, DocumentChunk, ProcessingStatus
from app.services.chat import ChatService
from app.services.retrieval import RetrievalService
from tests.conftest import FakeLLM

TOKENS = ("renewal", "security", "launch", "training")


class KeywordEmbeddings:
    def embed(self, texts):
        vectors = []
        for text in texts:
            values = [float(text.lower().count(token)) for token in TOKENS]
            magnitude = sqrt(sum(value * value for value in values)) or 1
            vectors.append([value / magnitude for value in values])
        return vectors


class EvaluatedVectorStore:
    def __init__(self):
        self.records: dict[str, VectorRecord] = {}
        self.filters: list[str] = []

    def upsert(self, records):
        self.records.update({record.id: record for record in records})

    def search(self, *, document_id, query_vector, top_k):
        self.filters.append(document_id)
        matches = []
        for record in self.records.values():
            if record.metadata["document_id"] != document_id:
                continue
            score = sum(left * right for left, right in zip(record.values, query_vector, strict=True))
            matches.append(VectorMatch(record.id, score))
        return sorted(matches, key=lambda match: match.score, reverse=True)[:top_k]


def make_document(document_id: str, chunks: list[str]) -> Document:
    document = Document(
        id=document_id,
        original_filename=f"{document_id}.txt",
        stored_filename=f"{document_id}.txt",
        content_type="text/plain",
        file_size=100,
        checksum=document_id * 16,
        processing_status=ProcessingStatus.ready,
        chunk_count=len(chunks),
    )
    document.chunks = [
        DocumentChunk(id=index + 1, chunk_index=index, text=text, vector_id=f"doc:{document_id}:chunk:{index}")
        for index, text in enumerate(chunks)
    ]
    return document


def index_document(store, embeddings, document):
    chunk_vectors = embeddings.embed([chunk.text for chunk in document.chunks])
    store.upsert(
        [
            VectorRecord(chunk.vector_id, vector, {"document_id": document.id, "chunk_id": chunk.id})
            for chunk, vector in zip(document.chunks, chunk_vectors, strict=True)
        ]
    )


def test_retrieval_evaluation_preserves_relevance_and_document_isolation():
    embeddings, store = KeywordEmbeddings(), EvaluatedVectorStore()
    commercial = make_document("commercial", ["Renewal is in September.", "Training is complete."])
    security = make_document("securityxx", ["Security review is required before launch."])
    index_document(store, embeddings, commercial)
    index_document(store, embeddings, security)

    retrieval = RetrievalService(embeddings, store, min_score=0.5)
    results = retrieval.retrieve(commercial, "When is renewal?", top_k=2)

    assert store.filters == ["commercial"]
    assert [result["text"] for result in results] == ["Renewal is in September."]
    assert all("Security review" not in result["text"] for result in results)


def test_retrieval_evaluation_returns_insufficient_evidence_without_llm_call():
    embeddings, store, llm = KeywordEmbeddings(), EvaluatedVectorStore(), FakeLLM()
    document = make_document("commercial", ["Renewal is in September."])
    index_document(store, embeddings, document)

    response = ChatService(RetrievalService(embeddings, store, min_score=0.5), llm).answer(
        document, "What security controls apply?", top_k=2
    )

    assert response.status == "insufficient_evidence"
    assert response.citations == []
    assert llm.calls == []
