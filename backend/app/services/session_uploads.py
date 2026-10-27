"""Stateless uploads: the browser retains extracted chunks and vectors for its tab."""

import hashlib
from math import sqrt
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from app.core.exceptions import IngestionError
from app.integrations.vector_store import VectorMatch
from app.models import Document, DocumentChunk, ProcessingStatus
from app.models.document import utcnow
from app.schemas.documents import SessionChunk, SessionDocument
from app.services.chunking import create_chunks
from app.services.extraction import extract_parts, validate_signature
from app.services.ingestion import ALLOWED_EXTENSIONS


def prepare_session_upload(filename: str, content_type: str, content: bytes, embeddings) -> SessionDocument:
    filename = Path(filename).name[:255]
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise IngestionError("Choose a TXT, PDF, or DOCX file")
    if not content or len(content) > 3 * 1024 * 1024:
        raise IngestionError("Choose a non-empty file no larger than 3 MB")
    if content_type and content_type not in ALLOWED_EXTENSIONS[extension]:
        raise IngestionError("File content type does not match its extension")
    validate_signature(extension, content)
    with TemporaryDirectory(prefix="clientops-upload-") as temporary:
        path = Path(temporary) / f"source{extension}"
        path.write_bytes(content)
        if extension == ".docx":
            try:
                with ZipFile(path) as archive:
                    members = archive.infolist()
                    if len(members) > 1000 or sum(member.file_size for member in members) > 20 * 1024 * 1024:
                        raise IngestionError("This DOCX expands beyond the demo's processing limit")
            except BadZipFile as exc:
                raise IngestionError("The DOCX file is unreadable or malformed") from exc
        if extension == ".pdf":
            import fitz

            try:
                with fitz.open(path) as pdf:
                    if pdf.page_count > 100:
                        raise IngestionError("The public demo supports PDFs up to 100 pages")
            except IngestionError:
                raise
            except (ValueError, RuntimeError) as exc:
                raise IngestionError("The PDF file is unreadable or malformed") from exc
        try:
            parts = extract_parts(path, extension)
        except (KeyError, BadZipFile) as exc:
            raise IngestionError("The document is unreadable or malformed") from exc
        if sum(len(part.text) for part in parts) > 32000:
            raise IngestionError("The public demo supports up to 32,000 extracted characters; choose a shorter file")
        chunks = create_chunks(parts)
    if not chunks:
        raise IngestionError("No readable text found. Scanned documents require OCR and are not supported")
    if len(chunks) > 60:
        raise IngestionError("This document has too many sections for the public demo; choose a shorter file")
    values = embeddings.embed([chunk.text for chunk in chunks])
    if len(values) != len(chunks):
        raise RuntimeError("Embedding provider returned an incomplete result")
    document_id = str(uuid4())
    return SessionDocument(
        id=document_id,
        filename=filename,
        content_type=content_type or sorted(ALLOWED_EXTENSIONS[extension])[0],
        file_size=len(content),
        checksum=hashlib.sha256(content).hexdigest(),
        chunks=[
            SessionChunk(
                id=index + 1,
                chunk_index=chunk.index,
                text=chunk.text,
                page_number=chunk.page_number,
                location=chunk.location,
                vector_id=f"session:{document_id}:{index}",
                embedding=value,
            )
            for index, (chunk, value) in enumerate(zip(chunks, values, strict=True))
        ],
    )


def session_document_model(source: SessionDocument) -> Document:
    document = Document(
        id=source.id,
        original_filename=source.filename,
        stored_filename=source.filename,
        content_type=source.content_type,
        file_size=source.file_size,
        checksum=source.checksum,
        processing_status=ProcessingStatus.ready,
        chunk_count=len(source.chunks),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    document.chunks = [
        DocumentChunk(
            id=chunk.id,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            page_number=chunk.page_number,
            location=chunk.location,
            vector_id=chunk.vector_id,
        )
        for chunk in source.chunks
    ]
    return document


class SessionVectorStore:
    def __init__(self, source: SessionDocument):
        self.source = source

    def search(self, *, document_id: str, query_vector: list[float], top_k: int) -> list[VectorMatch]:
        if document_id != self.source.id:
            return []
        magnitude = sqrt(sum(value * value for value in query_vector)) or 1
        matches = []
        for chunk in self.source.chunks:
            if len(query_vector) != len(chunk.embedding):
                raise ValueError("Upload session uses a different embedding model; upload the file again")
            norm = sqrt(sum(value * value for value in chunk.embedding)) or 1
            score = sum(a * b for a, b in zip(query_vector, chunk.embedding, strict=True)) / (magnitude * norm)
            matches.append(VectorMatch(chunk.vector_id, max(-1.0, min(1.0, score))))
        return sorted(matches, key=lambda match: match.score, reverse=True)[:top_k]
