from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.db.session import build_session_factory
from app.integrations.embeddings import PineconeInferenceEmbeddings
from app.integrations.vector_store import VectorRecord
from app.main import create_app
from app.models import Document
from app.services.demo_bootstrap import bootstrap_demo_metadata
from tests.conftest import FakeEmbeddings, FakeLLM, FakeVectors

SAMPLES = Path(__file__).resolve().parents[1] / "demo_documents"


def test_demo_metadata_survives_instance_replacement_with_stable_vector_ids(tmp_path):
    snapshots = []
    for name in ("first", "replacement"):
        sessions = build_session_factory(Settings(_env_file=None, database_url=f"sqlite:///{tmp_path / name}.db"))
        bootstrap_demo_metadata(sessions, SAMPLES)
        bootstrap_demo_metadata(sessions, SAMPLES)
        with sessions() as db:
            documents = db.query(Document).order_by(Document.id).all()
            assert len(documents) == 2
            snapshots.append([(doc.id, [(chunk.vector_id, chunk.text) for chunk in doc.chunks]) for doc in documents])
    assert snapshots[0] == snapshots[1]


def test_serverless_demo_bootstraps_before_requests_and_runs_scoped_chat(tmp_path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'demo.db'}",
        upload_directory=tmp_path / "uploads",
        demo_mode=True,
        serverless_demo_bootstrap=True,
        api_prefix="/api",
    )
    vectors, llm = FakeVectors(), FakeLLM()
    app = create_app(settings, embeddings=FakeEmbeddings(), vector_store=vectors, llm=llm)
    with app.state.session_factory() as db:
        for doc in db.query(Document).all():
            vectors.upsert([VectorRecord(chunk.vector_id, [1.0], {"document_id": doc.id}) for chunk in doc.chunks])

    # No lifespan context: serverless runtimes may serve a request without running it.
    client = TestClient(app)
    documents = client.get("/api/documents").json()["documents"]
    selected = documents[0]
    response = client.post(
        "/api/documents/chat", json={"document_id": selected["id"], "question": "Summarise the decisions"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "supported"
    assert llm.calls
    assert all(citation["document_id"] == selected["id"] for citation in response.json()["citations"])
    assert client.delete(f"/api/documents/{selected['id']}").status_code == 403
    assert client.post("/api/documents/upload", files={"file": ("x.txt", b"test", "text/plain")}).status_code == 403


def test_hosted_embeddings_distinguish_passages_from_queries(monkeypatch):
    calls = []

    def embed(**kwargs):
        calls.append(kwargs)
        return [SimpleNamespace(values=[0.5, 0.8]) for _ in kwargs["inputs"]]

    monkeypatch.setattr(
        "app.integrations.embeddings.Pinecone", lambda **_: SimpleNamespace(inference=SimpleNamespace(embed=embed))
    )
    provider = PineconeInferenceEmbeddings("test-key", "llama-text-embed-v2")
    assert provider.embed(["source"]) == [[0.5, 0.8]]
    assert provider.embed_query("question") == [0.5, 0.8]
    assert [call["parameters"]["input_type"] for call in calls] == ["passage", "query"]
