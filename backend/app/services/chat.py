import logging

from app.core.exceptions import ProviderError
from app.integrations.llm import LLMProvider
from app.models import Document
from app.schemas.documents import ChatResponse, Citation
from app.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, retrieval: RetrievalService, llm: LLMProvider):
        self.retrieval, self.llm = retrieval, llm

    def answer(self, document: Document, question: str, top_k: int) -> ChatResponse:
        retrieved = self.retrieval.retrieve(document, question, top_k)
        if not retrieved:
            return ChatResponse(
                document_id=document.id,
                filename=document.original_filename,
                question=question,
                answer="I could not find enough relevant evidence in this document to answer that question.",
                status="insufficient_evidence",
                citations=[],
            )
        citations = [
            Citation(
                document_id=document.id,
                filename=document.original_filename,
                chunk_id=item["chunk"].id,
                chunk_index=item["chunk"].chunk_index,
                page_number=item["chunk"].page_number,
                location=item["chunk"].location,
                relevance_score=round(item["score"], 4),
                source_preview=item["text"][:300],
            )
            for item in retrieved
        ]
        try:
            answer = self.llm.answer(question, retrieved)
        except ProviderError:
            logger.exception("LLM provider failed while answering document %s", document.id)
            return ChatResponse(
                document_id=document.id,
                filename=document.original_filename,
                question=question,
                answer="The answer provider is temporarily unavailable. Your document and citations remain intact.",
                status="provider_failure",
                citations=citations,
            )
        return ChatResponse(
            document_id=document.id,
            filename=document.original_filename,
            question=question,
            answer=answer,
            status="supported",
            citations=citations,
        )
