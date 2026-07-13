from dataclasses import dataclass
from pathlib import Path

import fitz
from docx import Document as DocxDocument

from app.core.exceptions import IngestionError


@dataclass(frozen=True)
class ExtractedPart:
    text: str
    page_number: int | None = None
    location: str | None = None


def extract_parts(path: Path, extension: str) -> list[ExtractedPart]:
    try:
        if extension == ".txt":
            text = path.read_text(encoding="utf-8")
            return [ExtractedPart(text=text, location="Text document")]
        if extension == ".pdf":
            with fitz.open(path) as pdf:
                if pdf.needs_pass:
                    raise IngestionError("Encrypted PDFs are not supported")
                return [
                    ExtractedPart(page.get_text("text"), page.number + 1, f"Page {page.number + 1}") for page in pdf
                ]
        if extension == ".docx":
            doc = DocxDocument(path)
            return [
                ExtractedPart(p.text, location=f"Paragraph {i + 1}")
                for i, p in enumerate(doc.paragraphs)
                if p.text.strip()
            ]
    except IngestionError:
        raise
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        raise IngestionError("The document is unreadable or malformed") from exc
    raise IngestionError("Unsupported document type")


def validate_signature(extension: str, content: bytes) -> None:
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise IngestionError("File contents do not match the .pdf extension")
    if extension == ".docx" and not content.startswith(b"PK"):
        raise IngestionError("File contents do not match the .docx extension")
    if extension == ".txt" and b"\x00" in content[:4096]:
        raise IngestionError("File contents do not appear to be plain text")
