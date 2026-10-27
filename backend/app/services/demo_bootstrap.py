import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Document, DocumentChunk, ProcessingStatus
from app.services.chunking import create_chunks
from app.services.extraction import ExtractedPart


def demo_document_id(filename: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"clientops-copilot-demo:{filename}"))


def bootstrap_demo_metadata(sessions: sessionmaker, samples: Path) -> None:
    engine = sessions.kw["bind"]
    Base.metadata.create_all(engine)
    with sessions() as db:
        if db.query(Document).first():
            return
        for path in sorted(samples.glob("*.txt")):
            content = path.read_bytes()
            text = content.decode("utf-8")
            document_id = demo_document_id(path.name)
            chunks = create_chunks([ExtractedPart(text=text, location="Text document")])
            document = Document(
                id=document_id,
                original_filename=path.name,
                stored_filename=path.name,
                content_type="text/plain",
                file_size=len(content),
                checksum=hashlib.sha256(content).hexdigest(),
                processing_status=ProcessingStatus.ready,
                chunk_count=len(chunks),
            )
            document.chunks.extend(
                DocumentChunk(
                    chunk_index=chunk.index,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    location=chunk.location,
                    vector_id=f"demo:{document_id}:chunk:{chunk.index}",
                )
                for chunk in chunks
            )
            db.add(document)
        db.commit()
