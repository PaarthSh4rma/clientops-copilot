from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Document


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, document_id: str, with_chunks: bool = False) -> Document | None:
        query = select(Document).where(Document.id == document_id)
        if with_chunks:
            query = query.options(selectinload(Document.chunks))
        return self.db.scalar(query)

    def list(self) -> list[Document]:
        return list(self.db.scalars(select(Document).order_by(Document.created_at.desc())))

    def add(self, document: Document) -> None:
        self.db.add(document)

    def delete(self, document: Document) -> None:
        self.db.delete(document)
