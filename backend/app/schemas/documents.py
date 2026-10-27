from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, FiniteFloat, model_validator

Workflow = Literal["summary", "decisions", "risks", "actions", "dates"]


class SessionChunk(BaseModel):
    id: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=1200)
    page_number: int | None = None
    location: str | None = Field(default=None, max_length=255)
    vector_id: str = Field(max_length=100)
    embedding: list[FiniteFloat] = Field(min_length=1, max_length=2048)


class SessionDocument(BaseModel):
    id: str = Field(min_length=1, max_length=36)
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(max_length=100)
    file_size: int = Field(ge=1, le=3 * 1024 * 1024)
    checksum: str = Field(min_length=64, max_length=64)
    chunks: list[SessionChunk] = Field(min_length=1, max_length=60)

    @model_validator(mode="after")
    def bound_context(self):
        if sum(len(chunk.text) for chunk in self.chunks) > 48000:
            raise ValueError("Document text exceeds the browser-session limit")
        dimensions = {len(chunk.embedding) for chunk in self.chunks}
        if len(dimensions) != 1 or len({chunk.id for chunk in self.chunks}) != len(self.chunks):
            raise ValueError("Invalid document chunk embeddings or identifiers")
        return self


class ChatContext(BaseModel):
    document_id: str
    question: str = Field(min_length=1, max_length=2000)
    chunk_ids: list[int] = Field(max_length=60)


class DocumentSummary(BaseModel):
    id: str
    filename: str
    content_type: str
    file_size: int
    checksum: str
    processing_status: str
    processing_error: str | None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class UploadResponse(DocumentSummary):
    preview: str
    message: str
    session_document: SessionDocument | None = None


class DocumentList(BaseModel):
    documents: list[DocumentSummary]


class ChatRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    workflow: Workflow | None = None
    context: ChatContext | None = None
    session_document: SessionDocument | None = None

    @model_validator(mode="after")
    def enforce_document_scope(self):
        if self.context and self.context.document_id != self.document_id:
            raise ValueError("Conversation context must belong to the selected document")
        if self.session_document and self.session_document.id != self.document_id:
            raise ValueError("Uploaded content must belong to the selected document")
        return self


class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_id: int
    chunk_index: int
    page_number: int | None
    location: str | None
    relevance_score: float | None
    source_preview: str


class ChatResponse(BaseModel):
    document_id: str
    filename: str
    question: str
    answer: str
    status: str
    citations: list[Citation]


class DeleteResponse(BaseModel):
    document_id: str
    deleted: bool
