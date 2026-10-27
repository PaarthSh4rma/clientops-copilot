from io import BytesIO

import fitz
import pytest
from docx import Document as DocxDocument
from fastapi.testclient import TestClient

from app.core.demo import DemoChatLimiter
from app.main import create_app
from tests.conftest import FakeEmbeddings, FakeLLM, FakeVectors, upload_txt


@pytest.mark.parametrize("workflow", ["summary", "decisions", "risks", "actions", "dates"])
def test_workflows_use_selected_source_even_without_semantic_matches(app_context, workflow):
    client, vectors, llm, _ = app_context
    selected = upload_txt(client, "selected.txt", "Casey owns key rotation by 12 December.")
    upload_txt(client, "other.txt", "Private material from a different document.")
    vectors.records = {}
    response = client.post(
        "/documents/chat",
        json={"document_id": selected["id"], "question": "Review this document", "workflow": workflow},
    )
    assert response.json()["status"] == "supported"
    assert {citation["document_id"] for citation in response.json()["citations"]} == {selected["id"]}
    assert all(citation["relevance_score"] is None for citation in response.json()["citations"])
    assert all("Private material" not in chunk["text"] for chunk in llm.calls[-1][1])


def test_follow_up_uses_cited_source_and_rejects_cross_document_context(app_context):
    client, vectors, llm, _ = app_context
    selected = upload_txt(client, "selected.txt", "Archived SKUs need client confirmation. Priya owns mapping.")
    other = upload_txt(client, "other.txt", "Unrelated confidential source.")
    first = client.post(
        "/documents/chat", json={"document_id": selected["id"], "question": "Find the risks", "workflow": "risks"}
    ).json()
    vectors.records = {}
    context = {
        "document_id": selected["id"],
        "question": first["question"],
        "chunk_ids": [citation["chunk_id"] for citation in first["citations"]],
    }
    payload = {"document_id": selected["id"], "question": "so what should we do?", "context": context}
    result = client.post("/documents/chat", json=payload).json()
    assert result["status"] == "supported"
    assert "Current question: so what should we do?" in llm.calls[-1][0]
    assert all("Archived SKUs" in chunk["text"] for chunk in llm.calls[-1][1])
    context["document_id"] = other["id"]
    assert client.post("/documents/chat", json=payload).status_code == 422


def test_unrelated_question_does_not_inherit_prior_evidence_or_consume_ai_budget(app_context):
    client, vectors, llm, settings = app_context
    selected = upload_txt(client)
    settings.demo_mode = True
    client.app.state.demo_chat_limiter = DemoChatLimiter(1)
    vectors.records = {}
    result = client.post(
        "/documents/chat",
        json={
            "document_id": selected["id"],
            "question": "What is the CEO's birthday?",
            "context": {"document_id": selected["id"], "question": "Summarise", "chunk_ids": [1]},
        },
    ).json()
    assert result["status"] == "insufficient_evidence"
    assert not llm.calls
    assert (
        client.post(
            "/documents/chat", json={"document_id": selected["id"], "question": "Summarise", "workflow": "summary"}
        ).json()["status"]
        == "supported"
    )


@pytest.mark.parametrize("extension", ["txt", "pdf", "docx"])
def test_browser_uploads_work_across_instances_without_shared_storage(app_context, extension):
    client, vectors, _, settings = app_context
    settings.demo_mode = True
    settings.allow_session_uploads = True
    text = "Project Aurora launches on 20 December 2026. Taylor owns the migration review."
    content, mime = text.encode(), "text/plain"
    if extension == "pdf":
        with fitz.open() as pdf:
            pdf.new_page().insert_text((72, 72), text)
            content = pdf.tobytes()
        mime = "application/pdf"
    elif extension == "docx":
        docx, output = DocxDocument(), BytesIO()
        docx.add_paragraph(text)
        docx.save(output)
        content = output.getvalue()
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    response = client.post("/documents/upload", files={"file": (f"aurora.{extension}", content, mime)})
    assert response.status_code == 201
    body = response.json()
    assert body["session_document"]["chunks"]
    assert not vectors.records
    assert client.get("/documents").json()["documents"] == []
    assert not list(settings.upload_directory.glob("*"))

    replacement = create_app(settings, embeddings=FakeEmbeddings(), vector_store=FakeVectors(), llm=FakeLLM())
    with TestClient(replacement) as second_client:
        chat = second_client.post(
            "/documents/chat",
            json={
                "document_id": body["id"],
                "question": body["session_document"]["chunks"][0]["text"],
                "session_document": body["session_document"],
            },
        )
        assert chat.json()["status"] == "supported"
        assert all(citation["document_id"] == body["id"] for citation in chat.json()["citations"])
        assert "Taylor" in chat.json()["citations"][0]["source_preview"]
        assert second_client.get(f"/documents/{body['id']}").status_code == 404


def test_session_upload_limits_and_sample_read_only_policy(app_context):
    client, _, _, settings = app_context
    sample = upload_txt(client)
    settings.demo_mode = True
    settings.allow_session_uploads = True
    assert client.get("/ready").json()["capabilities"]["session_uploads"] is True
    assert client.delete(f"/documents/{sample['id']}").status_code == 403
    assert client.post("/documents/upload", files={"file": ("big.txt", b"x" * 33000, "text/plain")}).status_code == 400
    assert (
        client.post("/documents/upload", files={"file": ("bad.exe", b"x", "application/octet-stream")}).status_code
        == 400
    )
