import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.integrations.file_storage import LocalFileStorage
from app.models import Document
from app.services.ingestion import IngestionService
from tests.conftest import FakeEmbeddings, FakeVectors


class FailingEmbeddings:
    def embed(self, texts):
        raise RuntimeError("embedding failed")


class FailingStorage(LocalFileStorage):
    def write(self, stored_filename, content):
        partial = self.path_for(stored_filename).with_suffix(".tmp")
        partial.write_bytes(b"partial")
        partial.unlink(missing_ok=True)
        raise OSError("disk failed")


def make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'cleanup.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False), engine


def test_embedding_failure_leaves_no_file_or_database_rows(tmp_path):
    sessions, _ = make_session(tmp_path)
    storage = LocalFileStorage(tmp_path / "uploads")
    with sessions() as db:
        service = IngestionService(db, storage, FailingEmbeddings(), FakeVectors(), 1024)
        with pytest.raises(RuntimeError, match="embedding failed"):
            service.ingest("failure.txt", "text/plain", b"valid source text")
    with sessions() as db:
        assert db.scalars(select(Document)).all() == []
    assert list(storage.root.iterdir()) == []


def test_final_commit_failure_compensates_vectors_files_and_rows(tmp_path, monkeypatch):
    sessions, _ = make_session(tmp_path)
    storage, vectors = LocalFileStorage(tmp_path / "uploads"), FakeVectors()
    with sessions() as db:
        service = IngestionService(db, storage, FakeEmbeddings(), vectors, 1024)
        monkeypatch.setattr(db, "commit", lambda: (_ for _ in ()).throw(RuntimeError("commit failed")))
        with pytest.raises(RuntimeError, match="commit failed"):
            service.ingest("failure.txt", "text/plain", b"valid source text")
    with sessions() as db:
        assert db.scalars(select(Document)).all() == []
    assert not vectors.records
    assert list(storage.root.iterdir()) == []


def test_file_persistence_failure_does_not_create_database_rows(tmp_path):
    sessions, _ = make_session(tmp_path)
    storage = FailingStorage(tmp_path / "uploads")
    with sessions() as db:
        service = IngestionService(db, storage, FakeEmbeddings(), FakeVectors(), 1024)
        with pytest.raises(OSError, match="disk failed"):
            service.ingest("failure.txt", "text/plain", b"valid source text")
    with sessions() as db:
        assert db.scalars(select(Document)).all() == []
    assert list(storage.root.iterdir()) == []
