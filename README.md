# ClientOps Copilot

AI-powered knowledge operations copilot for modern teams.

ClientOps Copilot is a full-stack Retrieval-Augmented Generation (RAG) platform that allows users to upload documents, semantically search them, and ask grounded questions using local embeddings and LLM-powered responses.

Built with a modular architecture focused on real-world AI systems engineering:
- document ingestion
- semantic chunk retrieval
- persistent vector storage
- grounded answer generation
- citation-backed responses

## Features

- Upload TXT, PDF, and DOCX documents
- Automatic document text extraction
- Intelligent chunking pipeline
- Local semantic embeddings using SentenceTransformers
- Persistent document + embedding storage with SQLite
- Semantic similarity search
- Grounded LLM-powered question answering
- Citation-backed responses
- Modular React + FastAPI architecture
- Local-first development workflow

## Architecture

```text
Upload Document
        ↓
Text Extraction
        ↓
Chunking Pipeline
        ↓
Local Embedding Generation
        ↓
SQLite Persistence
        ↓
Semantic Retrieval
        ↓
LLM Grounded Answer Generation
        ↓
Citation-backed Response
```


## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- TailwindCSS

### Backend
- FastAPI
- SQLAlchemy
- SQLite

### AI / ML
- SentenceTransformers
- OpenRouter
- Local embeddings
- Retrieval-Augmented Generation (RAG)

### Document Processing
- PyMuPDF
- python-docx

## Project Structure

```text
clientops-copilot/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── types/
│   │   └── App.tsx
│
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── embeddings.py
│   │   ├── extractors.py
│   │   ├── llm.py
│   │   ├── models.py
│   │   └── search.py
│   ├── uploads/
│   └── main.py
```

## How It Works

1. Users upload documents through the frontend dashboard
2. Backend extracts raw document text
3. Text is chunked into semantically searchable segments
4. SentenceTransformer embeddings are generated locally
5. Chunks + embeddings are persisted into SQLite
6. User questions are embedded and semantically matched
7. Top chunks are passed into the LLM context window
8. The LLM generates grounded responses backed by citations


## Local Setup

### Backend

```bash
cd backend

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

### Frontend

```bash
cd frontend

npm install
npm run dev
```

## Environment Variables

Create a `.env` file inside `backend/`:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openrouter/free
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/documents/upload` | Upload document |
| POST | `/documents/search` | Semantic chunk retrieval |
| POST | `/documents/chat` | Grounded RAG chat |
| GET | `/health` | Health check |

## Roadmap

- [x] Local RAG pipeline
- [x] Persistent embedding storage
- [x] PDF/DOCX ingestion
- [x] Citation-backed grounded answers
- [ ] Pinecone vector database
- [ ] Azure OpenAI support
- [ ] Conversational memory
- [ ] Multi-user authentication
- [ ] Cloud deployment

## Why I Built This

I built ClientOps Copilot to deepen my understanding of production-oriented AI systems engineering beyond simple LLM wrappers.

The goal was to explore:
- Retrieval-Augmented Generation (RAG)
- semantic search pipelines
- embedding architectures
- modular backend systems
- grounded AI responses
- full-stack AI application design

This project evolved from a simple upload-and-search prototype into a persistent full-stack AI knowledge platform with modular infrastructure and scalable architecture patterns.

## License

MIT