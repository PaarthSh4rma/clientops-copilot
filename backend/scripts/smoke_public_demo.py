"""Verify real public workflows and tab-scoped uploads using synthetic files only."""

import json
import sys
from io import BytesIO

import fitz
import httpx
from docx import Document as DocxDocument

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://clientops-copilot-psi.vercel.app"


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=120, headers={"X-Demo-Session": "release-smoke-v2"}) as client:
        ready = client.get("/api/ready")
        ready.raise_for_status()
        assert ready.json()["capabilities"]["session_uploads"]
        response = client.get("/api/documents")
        response.raise_for_status()
        samples = {document["filename"]: document for document in response.json()["documents"]}

        def ask(document_id, question, **extra):
            result = client.post(
                "/api/documents/chat", json={"document_id": document_id, "question": question, **extra}
            )
            result.raise_for_status()
            body = result.json()
            print(
                json.dumps(
                    {
                        "question": question,
                        "status": body["status"],
                        "answer": body["answer"],
                        "citations": len(body["citations"]),
                    }
                ),
                flush=True,
            )
            assert body["status"] == "supported" and body["citations"]
            assert all(citation["document_id"] == document_id for citation in body["citations"])
            return body

        security = samples["security_review.txt"]
        summary = ask(
            security["id"],
            "Summarise this document concisely. Focus on its purpose, scope, and most important details.",
            workflow="summary",
        )
        assert "rotation" in summary["answer"].lower()
        northstar = samples["client_success_plan.txt"]
        risks = ask(northstar["id"], "Identify risks and blockers in this document.", workflow="risks")
        ask(
            northstar["id"],
            "so what should we do?",
            context={
                "document_id": northstar["id"],
                "question": risks["question"],
                "chunk_ids": [citation["chunk_id"] for citation in risks["citations"]],
            },
        )

        text = (
            "Project Aurora customer migration. Taylor owns the mapping review. "
            "The pilot starts on 20 December 2026. The outstanding blocker is delivery of API credentials."
        )
        with fitz.open() as pdf:
            pdf.new_page().insert_textbox(fitz.Rect(50, 50, 550, 220), text, fontsize=11)
            pdf_bytes = pdf.tobytes()
        docx, docx_bytes = DocxDocument(), BytesIO()
        docx.add_paragraph(text)
        docx.save(docx_bytes)
        files = [
            ("aurora.txt", text.encode(), "text/plain"),
            ("aurora.pdf", pdf_bytes, "application/pdf"),
            (
                "aurora.docx",
                docx_bytes.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ]
        for filename, content, mime in files:
            uploaded = client.post("/api/documents/upload", files={"file": (filename, content, mime)})
            uploaded.raise_for_status()
            document = uploaded.json()
            assert document["session_document"]["chunks"]
            answer = ask(
                document["id"],
                "Who owns the mapping review, and when does the pilot start?",
                session_document=document["session_document"],
            )
            assert "Taylor" in answer["answer"] and "2026" in answer["answer"]
            assert client.get(f"/api/documents/{document['id']}").status_code == 404
            print(
                f"Verified {filename}: upload, live semantic retrieval, AI, citations, no shared document", flush=True
            )
        assert client.delete(f"/api/documents/{security['id']}").status_code == 403
        print("PUBLIC_DEMO_REGRESSION_PASSED", flush=True)


if __name__ == "__main__":
    main()
