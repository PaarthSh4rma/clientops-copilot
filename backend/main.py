from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.embeddings import embed_texts
from app.llm import generate_grounded_answer
import shutil
from pathlib import Path
import uuid
from pydantic import BaseModel
from app.search import rank_chunks
import ast
from app.extractors import extract_text
from sqlalchemy.orm import Session
from app.vectorstore import upsert_document_chunks
from app.vectorstore import semantic_search
from app.database import Base
from app.database import SessionLocal
from app.database import engine

from app.models import Document
from app.models import DocumentChunk

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

Base.metadata.create_all(bind=engine)

def build_grounded_answer(question: str, retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return (
            "I could not find enough relevant information in the uploaded document "
            "to answer that question."
        )

    best_chunk = retrieved_chunks[0]
    best_text = best_chunk["text"]

    return (
        "I found a relevant answer in the uploaded document.\n\n"
        f"The strongest matching source is chunk {best_chunk['chunk_index']} "
        f"with a similarity score of {best_chunk['score']}.\n\n"
        f"Relevant excerpt:\n\"{best_text[:500]}\""
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
    allowed_extensions = {".txt", ".pdf", ".docx"}    
    original_filename = file.filename or "uploaded-file"
    extension = Path(original_filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only .txt, .pdf and .docx files are supported for now."
        )

    document_id = str(uuid.uuid4())
    safe_filename = f"{document_id}{extension}"
    file_path = UPLOAD_DIR / safe_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        text = extract_text(file_path=file_path, extension=extension)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in this document."
        )
    
    chunks = chunk_text(text)

    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(chunk_texts)

    upsert_document_chunks(
    document_id=document_id,
    chunks=chunks,
    embeddings=embeddings,
)

    db: Session = SessionLocal()

    document_record = Document(
        id=document_id,
        filename=original_filename,
        content_type=file.content_type or "text/plain",
    )

    db.add(document_record)
    db.commit()

    for chunk, embedding in zip(chunks, embeddings):
        chunk_record = DocumentChunk(
            document_id=document_id,
            chunk_index=chunk["chunk_index"],
            text=chunk["text"],
            embedding=str(embedding),
        )

        db.add(chunk_record)

    db.commit()
    db.close()

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
        "message": "Document uploaded, text extracted, chunked, embedded, and persisted successfully",    
        }

@app.post("/documents/search")
def search_document(request: SearchRequest):
    db: Session = SessionLocal()

    document = (
        db.query(Document)
        .filter(Document.id == request.document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_records = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == request.document_id)
        .all()
    )

    chunks = []
    embeddings = []

    for record in chunk_records:
        chunks.append({
            "chunk_index": record.chunk_index,
            "text": record.text,
            "character_count": len(record.text),
        })

        embeddings.append(ast.literal_eval(record.embedding))

    query_embedding = embed_texts([request.query])[0]

    results = rank_chunks(
        query_embedding=query_embedding,
        chunks=chunks,
        chunk_embeddings=embeddings,
        top_k=request.top_k,
    )

    db.close()

    return {
        "document_id": request.document_id,
        "filename": document.filename,
        "query": request.query,
        "results": results,
    }

@app.post("/documents/chat")
def chat_with_document(request: ChatRequest):
    db: Session = SessionLocal()

    document = (
        db.query(Document)
        .filter(Document.id == request.document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_records = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == request.document_id)
        .all()
    )

    query_embedding = embed_texts([request.question])[0]
    chunks = []
    embeddings = []

    for record in chunk_records:
        chunks.append({
            "chunk_index": record.chunk_index,
            "text": record.text,
            "character_count": len(record.text),
        })

        embeddings.append(ast.literal_eval(record.embedding))

    pinecone_results = semantic_search(
        query_embedding=query_embedding,
        top_k=request.top_k,
    )

    retrieved_chunks = []

    for match in pinecone_results:
        retrieved_chunks.append(
            {
                "chunk_index": match.metadata["chunk_index"],
                "text": match.metadata["text"],
                "score": round(match.score, 4),
                "character_count": len(match.metadata["text"]),
            }
        )

    try:
        answer = generate_grounded_answer(
            question=request.question,
            retrieved_chunks=retrieved_chunks,
        )
        answer_mode = "llm"
    except Exception:
        answer = build_grounded_answer(
            question=request.question,
            retrieved_chunks=retrieved_chunks,
        )
        answer_mode = "fallback"

    citations = [
        {
            "chunk_index": chunk["chunk_index"],
            "score": chunk["score"],
            "source": document.filename,
            "preview": chunk["text"][:250],
        }
        for chunk in retrieved_chunks
    ]

    return {
        "document_id": request.document_id,
        "filename": document.filename,
        "question": request.question,
        "answer": answer,
        "answer_mode": answer_mode,
        "citations": citations,
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "clientops-copilot-api"
    }


