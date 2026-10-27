from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.base import Base
from app.db.session import build_engine
from app.integrations.file_storage import LocalFileStorage
from app.main import create_app
from tests.conftest import FakeEmbeddings, FakeLLM, FakeVectors


def test_comma_separated_cors_origins_parse_from_environment(monkeypatch):
    monkeypatch.setenv(
        "ALLOWED_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    assert Settings(_env_file=None).allowed_cors_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_production_requires_provider_configuration():
    settings = Settings(
        _env_file=None,
        app_environment="production",
        openrouter_api_key=None,
        pinecone_api_key=None,
        pinecone_index_name=None,
    )
    try:
        settings.validate_production_integrations()
    except RuntimeError as exc:
        assert "OPENROUTER_API_KEY" in str(exc)
        assert "PINECONE_API_KEY" in str(exc)
        assert "PINECONE_INDEX_NAME" in str(exc)
    else:
        raise AssertionError("Production configuration should reject missing providers")


def test_app_factory_settings_control_default_database_dependency(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'factory.db'}",
        upload_directory=tmp_path / "uploads",
    )
    Base.metadata.create_all(build_engine(settings))
    app = create_app(
        settings,
        embeddings=FakeEmbeddings(),
        vector_store=FakeVectors(),
        llm=FakeLLM(),
        storage=LocalFileStorage(settings.upload_directory),
    )
    with TestClient(app) as client:
        assert client.get("/documents").json() == {"documents": []}


def test_combined_deployment_serves_frontend_without_shadowing_api(tmp_path):
    frontend = tmp_path / "static"
    frontend.mkdir()
    (frontend / "index.html").write_text("<h1>ClientOps recruiter demo</h1>", encoding="utf-8")
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'combined.db'}",
        upload_directory=tmp_path / "uploads",
        frontend_directory=frontend,
    )
    Base.metadata.create_all(build_engine(settings))
    app = create_app(
        settings,
        embeddings=FakeEmbeddings(),
        vector_store=FakeVectors(),
        llm=FakeLLM(),
        storage=LocalFileStorage(settings.upload_directory),
    )
    with TestClient(app) as client:
        assert client.get("/").text == "<h1>ClientOps recruiter demo</h1>"
        assert client.get("/health").json()["status"] == "ok"


def test_blank_frontend_directory_is_disabled():
    assert Settings(_env_file=None, frontend_directory="").frontend_directory is None
