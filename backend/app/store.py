from typing import Any

DOCUMENT_STORE: dict[str, dict[str, Any]] = {}


def save_document(
    document_id: str,
    filename: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    DOCUMENT_STORE[document_id] = {
        "document_id": document_id,
        "filename": filename,
        "chunks": chunks,
        "embeddings": embeddings,
    }


def get_document(document_id: str) -> dict[str, Any] | None:
    return DOCUMENT_STORE.get(document_id)