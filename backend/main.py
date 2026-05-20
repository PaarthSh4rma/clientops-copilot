from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.embeddings import embed_texts
import shutil
from pathlib import Path
import uuid
from pydantic import BaseModel
from app.store import save_document, get_document
from app.search import rank_chunks

class SearchRequest(BaseModel):
    document_id: str
    query: str
    top_k: int = 3

class ChatRequest(BaseModel):
    document_id: str
    question: str
    top_k: int = 3

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
def build_grounded_answer(question: str, retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return "I could not find enough relevant information in the uploaded document to answer that."

    best_chunk = retrieved_chunks[0]

    return (
        "Based on the uploaded document, the most relevant information I found is:\n\n"
        f"\"{best_chunk['text']}\"\n\n"
        "This answer is grounded in the retrieved document context rather than general model knowledge."
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

    save_document(
    document_id=document_id,
    filename=original_filename,
    chunks=chunks,
    embeddings=embeddings,
    )

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

@app.post("/documents/search")
def search_document(request: SearchRequest):
    document = get_document(request.document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    query_embedding = embed_texts([request.query])[0]

    results = rank_chunks(
        query_embedding=query_embedding,
        chunks=document["chunks"],
        chunk_embeddings=document["embeddings"],
        top_k=request.top_k,
    )

    return {
        "document_id": request.document_id,
        "filename": document["filename"],
        "query": request.query,
        "results": results,
    }
@app.post("/documents/chat")
def chat_with_document(request: ChatRequest):
    document = get_document(request.document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    query_embedding = embed_texts([request.question])[0]

    retrieved_chunks = rank_chunks(
        query_embedding=query_embedding,
        chunks=document["chunks"],
        chunk_embeddings=document["embeddings"],
        top_k=request.top_k,
    )

    answer = build_grounded_answer(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
    )

    citations = [
        {
            "chunk_index": chunk["chunk_index"],
            "score": chunk["score"],
            "source": document["filename"],
            "preview": chunk["text"][:250],
        }
        for chunk in retrieved_chunks
    ]

    return {
        "document_id": request.document_id,
        "filename": document["filename"],
        "question": request.question,
        "answer": answer,
        "citations": citations,
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "clientops-copilot-api"
    }


