import hashlib

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
from app.services.chat import ChatService, document_workflow
from app.services.documents import DocumentLifecycleService
from app.services.ingestion import IngestionService
from app.services.retrieval import RetrievalService
from app.services.session_uploads import SessionVectorStore, prepare_session_upload, session_document_model

router = APIRouter(prefix="/documents", tags=["documents"])


def visitor_key(request: Request) -> str:
    session = request.headers.get("x-demo-session", "")[:128]
    identity = session or (request.client.host if request.client else "anonymous")
    return hashlib.sha256(identity.encode()).hexdigest()


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
    http_request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage=Depends(get_storage),
    embeddings=Depends(get_embeddings),
    vectors=Depends(get_vector_store),
    settings: Settings = Depends(get_app_settings),
):
    if settings.demo_mode and not settings.allow_session_uploads:
        raise HTTPException(status_code=403, detail="Uploads are disabled in the public demo")
    content = await file.read(settings.max_upload_size_bytes + 1)
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=400, detail="File exceeds the configured upload size limit")
    try:
        if settings.demo_mode and settings.allow_session_uploads:
            if not http_request.app.state.demo_upload_limiter.consume(visitor_key(http_request)):
                raise HTTPException(status_code=429, detail="This session has reached its hourly upload limit")
            session_source = await run_in_threadpool(
                prepare_session_upload,
                file.filename or "uploaded-file",
                file.content_type or "",
                content,
                embeddings,
            )
            document = session_document_model(session_source)
            return UploadResponse(
                **summary(document).model_dump(),
                preview=session_source.chunks[0].text[:500],
                message="Document ready in this browser tab. Refreshing clears uploaded documents.",
                session_document=session_source,
            )
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
    if request.session_document:
        if not settings.allow_session_uploads:
            raise HTTPException(status_code=403, detail="Browser-session uploads are disabled")
        document = session_document_model(request.session_document)
        vectors = SessionVectorStore(request.session_document)
    else:
        document = DocumentRepository(db).get(request.document_id, with_chunks=True)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.processing_status is not ProcessingStatus.ready:
        raise HTTPException(status_code=409, detail="Document is not ready for questions")
    workflow = request.workflow or document_workflow(request.question)
    cache = http_request.app.state.demo_answer_cache
    cache_key = None
    if settings.demo_mode and request.session_document is None:
        context_key = request.context.model_dump_json() if request.context and not workflow else ""
        cache_key = hashlib.sha256(
            f"{document.id}:{document.checksum}:{workflow}:{request.question}:{context_key}".encode()
        ).hexdigest()
        cached = cache.get(cache_key)
        if cached:
            return cached

    def consume_question():
        if settings.demo_mode and not http_request.app.state.demo_chat_limiter.consume(visitor_key(http_request)):
            raise HTTPException(
                status_code=429,
                detail="Your demo session has reached its hourly AI limit. Cached sample answers still work.",
                headers={"Retry-After": "3600"},
            )

    retrieval = RetrievalService(embeddings, vectors, settings.retrieval_min_score)
    try:
        response = ChatService(retrieval, llm).answer(
            document,
            request.question,
            request.top_k or settings.retrieval_top_k,
            workflow=workflow,
            context=request.context,
            before_answer=consume_question,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if cache_key and response.status == "supported":
        cache.put(cache_key, response)
    return response


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
