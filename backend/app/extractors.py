from pathlib import Path

import fitz
from docx import Document as DocxDocument


def extract_text_from_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def extract_text_from_pdf(file_path: Path) -> str:
    text_parts: list[str] = []

    with fitz.open(file_path) as pdf:
        for page in pdf:
            text_parts.append(page.get_text("text"))

    return "\n\n".join(text_parts).strip()


def extract_text_from_docx(file_path: Path) -> str:
    document = DocxDocument(file_path)

    paragraphs = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n\n".join(paragraphs)


def extract_text(file_path: Path, extension: str) -> str:
    if extension == ".txt":
        return extract_text_from_txt(file_path)

    if extension == ".pdf":
        return extract_text_from_pdf(file_path)

    if extension == ".docx":
        return extract_text_from_docx(file_path)

    raise ValueError(f"Unsupported file extension: {extension}")