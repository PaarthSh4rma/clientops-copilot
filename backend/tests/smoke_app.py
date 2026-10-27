"""Credential-free HTTP smoke application used by release acceptance checks."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.core.exceptions import ProviderError
from app.db.base import Base
from app.db.session import get_db
from app.integrations.file_storage import LocalFileStorage
from app.main import create_app
from tests.conftest import FakeEmbeddings, FakeLLM, FakeVectors


class SmokeEmbeddings(FakeEmbeddings):
    def embed(self, texts):
        return [[-1.0, 1.0] if text == "no evidence" else [float(len(text) % 7), 1.0] for text in texts]


class SmokeVectors(FakeVectors):
    def search(self, *, document_id, query_vector, top_k):
        if query_vector[0] == -1.0:
            self.search_document_id = document_id
            self.search_top_k = top_k
            return []
        return super().search(document_id=document_id, query_vector=query_vector, top_k=top_k)


class SmokeLLM(FakeLLM):
    def answer(self, question, chunks):
        if question == "provider failure":
            raise ProviderError("simulated provider failure")
        return super().answer(question, chunks)


settings = Settings(
    app_environment="test",
    database_url="sqlite:////tmp/clientops-http-smoke.db",
    upload_directory="/tmp/clientops-http-smoke-uploads",
    max_upload_size_bytes=10 * 1024 * 1024,
)
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
sessions = sessionmaker(bind=engine, expire_on_commit=False)
vectors = SmokeVectors()
llm = SmokeLLM()
app = create_app(
    settings,
    embeddings=SmokeEmbeddings(),
    vector_store=vectors,
    llm=llm,
    storage=LocalFileStorage(settings.upload_directory),
)


def smoke_db():
    db = sessions()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = smoke_db
