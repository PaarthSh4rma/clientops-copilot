from app.services.chunking import create_chunks
from app.services.extraction import extract_parts


def test_txt_extraction_and_chunk_creation(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("first paragraph\n\nsecond paragraph")
    parts = extract_parts(path, ".txt")
    chunks = create_chunks(parts, chunk_size=100, overlap=10)
    assert "first paragraph" in parts[0].text
    assert chunks and chunks[0].location == "Text document"
