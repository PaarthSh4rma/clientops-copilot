from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.embeddings import embed_texts
import shutil
from pathlib import Path
import uuid

app = FastAPI(
    title="ClientOps Copilot API",
    description="AI-powered operations copilot backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def chunk_text(text: str) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    chunks = splitter.split_text(text)

    return [
        {
            "chunk_index": index,
            "text": chunk,
            "character_count": len(chunk),
        }
        for index, chunk in enumerate(chunks)
    ]

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    allowed_extensions = {".txt"}
    original_filename = file.filename or "uploaded-file"
    extension = Path(original_filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported for now."
        )

    document_id = str(uuid.uuid4())
    safe_filename = f"{document_id}{extension}"
    file_path = UPLOAD_DIR / safe_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = file_path.read_text(encoding="utf-8")
    chunks = chunk_text(text)

    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(chunk_texts)

    return {
        "document_id": document_id,
        "filename": original_filename,
        "stored_as": safe_filename,
        "content_type": file.content_type,
        "character_count": len(text),
        "chunk_count": len(chunks),
        "preview": text[:500],
        "chunks_preview": chunks[:3],
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimensions": len(embeddings[0]) if embeddings else 0,
        "embedded_chunk_count": len(embeddings),
        "message": "Document uploaded and text extracted successfully",
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "clientops-copilot-api"
    }


