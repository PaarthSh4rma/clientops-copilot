import logging
import re
from collections.abc import Callable

from app.core.exceptions import ProviderError
from app.integrations.llm import LLMProvider
from app.models import Document
from app.schemas.documents import ChatContext, ChatResponse, Citation, Workflow
from app.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)


def document_workflow(question: str) -> Workflow | None:
    clean = question.strip().lower()
    for prefix, workflow in (
        ("summarise", "summary"),
        ("summarize", "summary"),
        ("extract the key decisions", "decisions"),
        ("identify risks, blockers", "risks"),
        ("extract action items", "actions"),
        ("find important dates", "dates"),
    ):
        if clean.startswith(prefix):
            return workflow
    return None


def is_follow_up(question: str) -> bool:
    return bool(
        re.search(
            r"\b(so what|what should we|what do we|what about (?:that|this|those|these)|"
            r"tell me more|explain (?:that|this|those)|how (?:can|should) we|what next)\b",
            question.lower(),
        )
    )


class ChatService:
    def __init__(self, retrieval: RetrievalService, llm: LLMProvider):
        self.retrieval, self.llm = retrieval, llm

    def answer(
        self,
        document: Document,
        question: str,
        top_k: int,
        *,
        workflow: Workflow | None = None,
        context: ChatContext | None = None,
        before_answer: Callable[[], None] | None = None,
    ) -> ChatResponse:
        workflow = workflow or document_workflow(question)
        provider_question = question
        if workflow:
            retrieved = self.retrieval.document_passages(document)
        elif context and context.document_id == document.id and is_follow_up(question):
            retrieved = self.retrieval.document_passages(document, context.chunk_ids)
            provider_question = (
                f"Previous question, for conversation reference only: {context.question}\n"
                f"Current question: {question}\n"
                "Answer the current question from the supplied document evidence. "
                "Separate source-stated commitments from suggested next steps."
            )
            if not retrieved:
                retrieved = self.retrieval.retrieve(document, question, top_k)
        else:
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
                relevance_score=round(item["score"], 4) if item["score"] is not None else None,
                source_preview=item["text"],
            )
            for item in retrieved
        ]
        if before_answer:
            before_answer()
        try:
            answer = self.llm.answer(provider_question, retrieved)
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
