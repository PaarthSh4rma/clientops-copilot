from pathlib import Path

import fitz
from docx import Document as DocxDocument

from tests.conftest import upload_txt


def test_supported_upload_persistence_and_listing(client):
    document = upload_txt(client)
    listed = client.get("/documents").json()["documents"]
    assert listed[0]["id"] == document["id"]
    assert document["chunk_count"] > 0


def test_unsupported_upload(client):
    response = client.post("/documents/upload", files={"file": ("bad.exe", b"abc", "application/octet-stream")})
    assert response.status_code == 400


def test_pdf_and_docx_upload_preserve_source_locations(client, tmp_path):
    pdf_path = tmp_path / "source.pdf"
    with fitz.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Renewal occurs in September.")
        pdf.save(pdf_path)
    pdf_response = client.post(
        "/documents/upload", files={"file": ("source.pdf", pdf_path.read_bytes(), "application/pdf")}
    )
    assert pdf_response.status_code == 201
    pdf_chat = client.post(
        "/documents/chat",
        json={"document_id": pdf_response.json()["id"], "question": "When is renewal?"},
    ).json()
    assert pdf_chat["citations"][0]["page_number"] == 1

    docx_path = tmp_path / "source.docx"
    docx = DocxDocument()
    docx.add_paragraph("The implementation owner is Priya.")
    docx.save(docx_path)
    docx_response = client.post(
        "/documents/upload",
        files={
            "file": (
                "source.docx",
                docx_path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert docx_response.status_code == 201
    docx_chat = client.post(
        "/documents/chat",
        json={"document_id": docx_response.json()["id"], "question": "Who owns implementation?"},
    ).json()
    assert docx_chat["citations"][0]["location"] == "Paragraph 1"


def test_malformed_and_mismatched_documents_are_rejected(client):
    malformed = client.post("/documents/upload", files={"file": ("broken.pdf", b"%PDF-not-valid", "application/pdf")})
    mismatch = client.post("/documents/upload", files={"file": ("plain.pdf", b"plain text", "application/pdf")})
    wrong_mime = client.post("/documents/upload", files={"file": ("plain.txt", b"plain text", "application/pdf")})
    assert malformed.status_code == 400
    assert mismatch.status_code == 400
    assert wrong_mime.status_code == 400


def test_size_and_empty_rejection(app_context):
    client, _, _, settings = app_context
    settings.max_upload_size_bytes = 3
    assert client.post("/documents/upload", files={"file": ("big.txt", b"1234", "text/plain")}).status_code == 400
    assert client.post("/documents/upload", files={"file": ("empty.txt", b"", "text/plain")}).status_code == 400


def test_missing_document_and_top_k_validation(client):
    assert client.get("/documents/missing").status_code == 404
    response = client.post("/documents/chat", json={"document_id": "missing", "question": "hello", "top_k": 0})
    assert response.status_code == 422


def test_missing_document_never_searches_globally(client, app_context):
    _, vectors, _, _ = app_context
    response = client.post("/documents/chat", json={"document_id": "missing", "question": "hello"})
    assert response.status_code == 404
    assert vectors.search_document_id is None


def test_document_scoped_retrieval(client, app_context):
    _, vectors, _, _ = app_context
    first = upload_txt(client, "a.txt", "Alpha contract material")
    second = upload_txt(client, "b.txt", "Beta onboarding material")
    response = client.post("/documents/chat", json={"document_id": second["id"], "question": "onboarding", "top_k": 4})
    assert response.status_code == 200
    assert vectors.search_document_id == second["id"]
    assert all(c["document_id"] == second["id"] for c in response.json()["citations"])
    assert all("Beta onboarding" in c["source_preview"] for c in response.json()["citations"])
    assert all("Alpha contract" not in c["source_preview"] for c in response.json()["citations"])
    first_ids = {key for key in vectors.records if first["id"] in key}
    second_ids = {key for key in vectors.records if second["id"] in key}
    assert first_ids.isdisjoint(second_ids)
    assert any(key.endswith(":chunk:0") for key in first_ids)
    assert any(key.endswith(":chunk:0") for key in second_ids)


def test_insufficient_evidence_and_provider_failure(client, app_context):
    _, vectors, llm, _ = app_context
    document = upload_txt(client)
    vectors.records = {}
    response = client.post("/documents/chat", json={"document_id": document["id"], "question": "unknown"})
    assert response.json()["status"] == "insufficient_evidence"
    assert llm.calls == []
    upload_txt(client, "again.txt", "Provider failure evidence")
    llm.fail = True
    response = client.post(
        "/documents/chat",
        json={"document_id": client.get("/documents").json()["documents"][0]["id"], "question": "evidence"},
    )
    assert response.json()["status"] == "provider_failure"


def test_delete_cleans_vectors_and_file(client, app_context):
    _, vectors, _, settings = app_context
    document = upload_txt(client)
    assert vectors.records
    response = client.delete(f"/documents/{document['id']}")
    assert response.status_code == 200
    assert not vectors.records
    assert vectors.delete_document_ids == [document["id"]]
    assert not list(Path(settings.upload_directory).glob(f"{document['id']}.*"))
    assert client.get(f"/documents/{document['id']}").status_code == 404
    assert client.post("/documents/chat", json={"document_id": document["id"], "question": "hello"}).status_code == 404
    assert client.delete(f"/documents/{document['id']}").status_code == 404


def test_delete_failure_is_not_reported_as_success(client, app_context):
    _, vectors, _, _ = app_context
    document = upload_txt(client)
    vectors.fail_delete = True
    response = client.delete(f"/documents/{document['id']}")
    assert response.status_code == 503
    detail = client.get(f"/documents/{document['id']}").json()
    assert detail["processing_status"] == "failed"
    assert detail["processing_error"]
    chat = client.post(
        "/documents/chat",
        json={"document_id": document["id"], "question": "Should not run"},
    )
    assert chat.status_code == 409


def test_failed_ingestion_cleans_source(app_context):
    client, vectors, _, settings = app_context
    vectors.fail_upsert = True
    vectors.partial_upsert = True
    response = client.post("/documents/upload", files={"file": ("fail.txt", b"valid text", "text/plain")})
    assert response.status_code == 503
    assert not list(Path(settings.upload_directory).glob("*.txt"))
    assert not vectors.records


def test_health_and_readiness(client):
    assert client.get("/health").json()["status"] == "ok"
    readiness = client.get("/ready").json()
    assert readiness["status"] == "ready"
    assert readiness["limits"]["max_upload_size_bytes"] == 10 * 1024 * 1024
    assert client.get("/openapi.json").json()["info"]["version"] == "0.1.5"


def test_readiness_degrades_when_vector_store_is_unavailable(client, app_context):
    _, vectors, _, _ = app_context
    vectors.ready = lambda: False
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["dependencies"]["vector_store"] == "unavailable"


def test_configured_default_top_k_is_used(client, app_context):
    _, vectors, _, settings = app_context
    settings.retrieval_top_k = 7
    document = upload_txt(client)
    client.post("/documents/chat", json={"document_id": document["id"], "question": "contract"})
    assert vectors.search_document_id == document["id"]
    assert vectors.search_top_k == 7
