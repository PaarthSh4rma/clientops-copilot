import hashlib
import logging
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateDocumentError, IngestionError
from app.integrations.embeddings import EmbeddingProvider
from app.integrations.file_storage import LocalFileStorage
from app.integrations.vector_store import VectorRecord, VectorStore
from app.models import Document, DocumentChunk, ProcessingStatus
from app.repositories.documents import DocumentRepository
from app.services.chunking import create_chunks
from app.services.extraction import extract_parts, validate_signature

logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {
    ".txt": {"text/plain"},
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"},
}


class IngestionService:
    def __init__(
        self, db: Session, storage: LocalFileStorage, embeddings: EmbeddingProvider, vectors: VectorStore, max_size: int
    ):
        self.db, self.storage, self.embeddings, self.vectors, self.max_size = db, storage, embeddings, vectors, max_size

    def ingest(self, filename: str, content_type: str, content: bytes) -> tuple[Document, str]:
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise IngestionError("Only .txt, .pdf and .docx files are supported")
        if len(content) > self.max_size:
            raise IngestionError(f"File exceeds the {self.max_size}-byte upload limit")
        if not content:
            raise IngestionError("The uploaded file is empty")
        if content_type and content_type not in ALLOWED_EXTENSIONS[extension]:
            raise IngestionError("File content type does not match its extension")
        validate_signature(extension, content)

        document_id = str(uuid4())
        stored_filename = f"{document_id}{extension}"
        checksum = hashlib.sha256(content).hexdigest()
        existing = DocumentRepository(self.db).get_by_checksum(checksum)
        if existing:
            raise DuplicateDocumentError(existing.id, existing.original_filename)
        path = self.storage.write(stored_filename, content)
        vector_upsert_attempted = False
        try:
            parts = extract_parts(path, extension)
            chunks = create_chunks(parts)
            if not chunks:
                raise IngestionError("No extractable text found in this document")
            values = self.embeddings.embed([chunk.text for chunk in chunks])
            if len(values) != len(chunks):
                raise IngestionError("Embedding provider returned an incomplete result")
            document = Document(
                id=document_id,
                original_filename=Path(filename).name,
                stored_filename=stored_filename,
                content_type=content_type or ALLOWED_EXTENSIONS[extension].copy().pop(),
                file_size=len(content),
                checksum=checksum,
                processing_status=ProcessingStatus.processing,
                chunk_count=len(chunks),
            )
            for chunk in chunks:
                document.chunks.append(
                    DocumentChunk(
                        chunk_index=chunk.index,
                        text=chunk.text,
                        page_number=chunk.page_number,
                        location=chunk.location,
                        vector_id=f"doc:{document_id}:chunk:{chunk.index}",
                    )
                )
            DocumentRepository(self.db).add(document)
            self.db.flush()
            vector_upsert_attempted = True
            self.vectors.upsert(
                [
                    VectorRecord(c.vector_id, value, {"document_id": document_id, "chunk_id": c.id})
                    for c, value in zip(document.chunks, values, strict=True)
                ]
            )
            document.processing_status = ProcessingStatus.ready
            self.db.commit()
            self.db.refresh(document)
            return document, chunks[0].text[:500]
        except Exception:
            self.db.rollback()
            if vector_upsert_attempted:
                try:
                    self.vectors.delete_document(document_id)
                except Exception:
                    logger.exception("Compensating vector cleanup failed for document %s", document_id)
            self.storage.delete(stored_filename)
            raise
