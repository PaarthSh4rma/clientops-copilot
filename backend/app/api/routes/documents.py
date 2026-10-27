from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.exceptions import DuplicateDocumentError, IngestionError
from app.db.session import get_db
from app.dependencies import get_app_settings, get_embeddings, get_llm, get_storage, get_vector_store
from app.models import ProcessingStatus
from app.repositories.documents import DocumentRepository
from app.schemas.documents import (
    ChatRequest,
    ChatResponse,
    DeleteResponse,
    DocumentList,
    DocumentSummary,
    UploadResponse,
)
from app.services.chat import ChatService
from app.services.documents import DocumentLifecycleService
from app.services.ingestion import IngestionService
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/documents", tags=["documents"])


def summary(document) -> DocumentSummary:
    return DocumentSummary(
        id=document.id,
        filename=document.original_filename,
        content_type=document.content_type,
        file_size=document.file_size,
        checksum=document.checksum,
        processing_status=document.processing_status.value,
        processing_error=document.processing_error,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
    embeddings=Depends(get_embeddings),
    vectors=Depends(get_vector_store),
    settings: Settings = Depends(get_app_settings),
):
    if settings.demo_mode:
        raise HTTPException(status_code=403, detail="Uploads are disabled in the public demo")
    content = await file.read(settings.max_upload_size_bytes + 1)
    try:
        document, preview = await run_in_threadpool(
            IngestionService(db, storage, embeddings, vectors, settings.max_upload_size_bytes).ingest,
            file.filename or "uploaded-file",
            file.content_type or "",
            content,
        )
    except DuplicateDocumentError as exc:
        raise HTTPException(
            status_code=409,
            detail={"message": str(exc), "document_id": exc.document_id, "code": "duplicate_document"},
        ) from exc
    except IngestionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Document indexing is temporarily unavailable") from exc
    return UploadResponse(**summary(document).model_dump(), preview=preview, message="Document indexed successfully")


@router.get("", response_model=DocumentList)
def list_documents(db: Session = Depends(get_db)):
    return DocumentList(documents=[summary(doc) for doc in DocumentRepository(db).list()])


@router.get("/{document_id}", response_model=DocumentSummary)
def get_document(document_id: str, db: Session = Depends(get_db)):
    document = DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return summary(document)


@router.post("/chat", response_model=ChatResponse)
def chat_document(
    request: ChatRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    embeddings=Depends(get_embeddings),
    vectors=Depends(get_vector_store),
    llm=Depends(get_llm),
    settings: Settings = Depends(get_app_settings),
):
    document = DocumentRepository(db).get(request.document_id, with_chunks=True)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.processing_status is not ProcessingStatus.ready:
        raise HTTPException(status_code=409, detail="Document is not ready for questions")
    if settings.demo_mode and not http_request.app.state.demo_chat_limiter.consume():
        raise HTTPException(
            status_code=429,
            detail="The public demo has reached its hourly question limit. Please try again later or run locally.",
        )
    retrieval = RetrievalService(embeddings, vectors, settings.retrieval_min_score)
    return ChatService(retrieval, llm).answer(document, request.question, request.top_k or settings.retrieval_top_k)


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
    vectors=Depends(get_vector_store),
    settings: Settings = Depends(get_app_settings),
):
    if settings.demo_mode:
        raise HTTPException(status_code=403, detail="Deletion is disabled in the public demo")
    document = DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        DocumentLifecycleService(db, storage, vectors).delete(document)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Document cleanup is temporarily unavailable") from exc
    return DeleteResponse(document_id=document_id, deleted=True)
