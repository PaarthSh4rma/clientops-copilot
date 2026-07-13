from datetime import datetime

from pydantic import BaseModel, Field


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


class DocumentList(BaseModel):
    documents: list[DocumentSummary]


class ChatRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_id: int
    chunk_index: int
    page_number: int | None
    location: str | None
    relevance_score: float
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
