from app.integrations.embeddings import EmbeddingProvider
from app.integrations.vector_store import VectorStore
from app.models import Document


class RetrievalService:
    def __init__(self, embeddings: EmbeddingProvider, vectors: VectorStore, min_score: float):
        self.embeddings, self.vectors, self.min_score = embeddings, vectors, min_score

    def retrieve(self, document: Document, question: str, top_k: int) -> list[dict]:
        query_vector = self.embeddings.embed([question])[0]
        matches = self.vectors.search(document_id=document.id, query_vector=query_vector, top_k=top_k)
        by_vector = {chunk.vector_id: chunk for chunk in document.chunks}
        return [
            {"chunk": by_vector[match.id], "text": by_vector[match.id].text, "score": match.score}
            for match in matches
            if match.score >= self.min_score and match.id in by_vector
        ]
