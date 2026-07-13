import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db
from app.integrations.file_storage import LocalFileStorage
from app.integrations.vector_store import VectorMatch
from app.main import create_app


class FakeEmbeddings:
    def embed(self, texts):
        return [[float(len(text) % 7), 1.0] for text in texts]


class FakeVectors:
    def __init__(self):
        self.records = {}
        self.search_document_id = None
        self.search_top_k = None
        self.delete_document_ids = []
        self.fail_upsert = False
        self.partial_upsert = False
        self.fail_delete = False

    def upsert(self, records):
        if self.fail_upsert:
            if self.partial_upsert and records:
                self.records[records[0].id] = records[0]
            raise RuntimeError("upsert failed")
        self.records.update({record.id: record for record in records})

    def search(self, *, document_id, query_vector, top_k):
        self.search_document_id = document_id
        self.search_top_k = top_k
        return [
            VectorMatch(id=key, score=0.9)
            for key, record in self.records.items()
            if record.metadata["document_id"] == document_id
        ][:top_k]

    def delete_document(self, document_id):
        self.delete_document_ids.append(document_id)
        if self.fail_delete:
            raise RuntimeError("delete failed")
        self.records = {
            key: value for key, value in self.records.items() if value.metadata["document_id"] != document_id
        }

    def ready(self):
        return True


class FakeLLM:
    fail = False

    def __init__(self):
        self.calls = []

    def answer(self, question, chunks):
        self.calls.append((question, chunks))
        if self.fail:
            from app.core.exceptions import ProviderError

            raise ProviderError("failed")
        return "Supported by the selected document."

    def configured(self):
        return True


@pytest.fixture
def app_context(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    vectors, llm = FakeVectors(), FakeLLM()
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        upload_directory=tmp_path / "uploads",
        retrieval_min_score=0.25,
    )
    app = create_app(
        settings,
        embeddings=FakeEmbeddings(),
        vector_store=vectors,
        llm=llm,
        storage=LocalFileStorage(settings.upload_directory),
    )

    def db_override():
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_override
    with TestClient(app) as client:
        yield client, vectors, llm, settings


@pytest.fixture
def client(app_context):
    return app_context[0]


def upload_txt(
    client, name="sample.txt", text="A useful client contract includes a renewal date and delivery commitments."
):
    response = client.post("/documents/upload", files={"file": (name, text.encode(), "text/plain")})
    assert response.status_code == 201, response.text
    return response.json()
