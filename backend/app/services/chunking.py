from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.extraction import ExtractedPart


@dataclass(frozen=True)
class ChunkData:
    index: int
    text: str
    page_number: int | None
    location: str | None


def create_chunks(parts: list[ExtractedPart], chunk_size: int = 800, overlap: int = 150) -> list[ChunkData]:
    if not 100 <= chunk_size <= 4000 or not 0 <= overlap < chunk_size:
        raise ValueError("Invalid chunk bounds")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = []
    for part in parts:
        for text in splitter.split_text(part.text.strip()):
            if text.strip():
                chunks.append(ChunkData(len(chunks), text, part.page_number, part.location))
    return chunks
