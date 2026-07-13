import logging

from sqlalchemy.orm import Session

from app.integrations.file_storage import LocalFileStorage
from app.integrations.vector_store import VectorStore
from app.models import Document, ProcessingStatus

logger = logging.getLogger(__name__)


class DocumentLifecycleService:
    def __init__(self, db: Session, storage: LocalFileStorage, vectors: VectorStore):
        self.db, self.storage, self.vectors = db, storage, vectors

    def delete(self, document: Document) -> None:
        try:
            self.vectors.delete_document(document.id)
            self.storage.delete(document.stored_filename)
            self.db.delete(document)
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.exception("Document deletion failed for %s", document.id)
            try:
                document.processing_status = ProcessingStatus.failed
                document.processing_error = "Deletion was interrupted; retry deletion"
                self.db.add(document)
                self.db.commit()
            except Exception:
                self.db.rollback()
                logger.exception("Could not record interrupted deletion for %s", document.id)
            raise RuntimeError("Document deletion was interrupted") from exc
