# ClientOps Copilot

ClientOps Copilot is a portfolio project and evolving product prototype for agencies, consultancies, implementation teams, and customer-success teams. It provides a single workspace where users can index client documents and ask source-grounded questions without manually searching contracts, briefs, SOPs, onboarding files, and project material.

**v1.5 is a trustworthy single-workspace foundation—not a production-ready or multi-tenant SaaS product.**

## What v1.5 does

- uploads TXT, PDF, and DOCX files up to a configurable limit
- validates file extension, reported content type, and basic file signatures
- preserves PDF pages and useful DOCX/TXT locations in citations
- stores source files locally, metadata/chunk text in SQLite, and vectors in Pinecone
- scopes every similarity query and deletion to one document
- answers through OpenRouter only when retrieval clears a configurable relevance threshold
- distinguishes supported answers, insufficient evidence, and provider failure
- lists, selects, inspects, and deletes documents through real lifecycle APIs
- reports liveness separately from dependency readiness

It does **not** provide authentication, organisations, tenant isolation, durable conversation memory, OCR, asynchronous ingestion, encrypted object storage, or production operations. It cannot guarantee hallucination-free answers.

## Architecture

React/Vite calls a FastAPI API. Routes delegate to ingestion, retrieval, chat, and lifecycle services. SQLite is authoritative for document/chunk metadata and vector IDs; Pinecone is authoritative for vectors; a file-storage interface currently writes source files locally. SentenceTransformers creates embeddings and OpenRouter generates answers from retrieved context.

See [architecture](docs/ARCHITECTURE.md), [product audit](docs/PRODUCT_AUDIT.md), and [roadmap](docs/ROADMAP.md).

## Local setup

Prerequisites: Python 3.11+, Node 22+, a Pinecone index matching the embedding model dimensions, and OpenRouter/Pinecone credentials.

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# add provider credentials
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

The UI defaults to `http://localhost:8000`. Override it with `VITE_API_BASE_URL` at frontend build time. Development CORS permits the `localhost:5173` and `127.0.0.1:5173` loopback origins by default.

Existing prototype databases contain stringified embeddings and do not match the v1.5 model. Because they are development-only artifacts, recreate them and run `alembic upgrade head`; source files/vectors from the old prototype should be manually cleared. Future schema changes should use Alembic migrations.

## Configuration

`backend/.env.example` documents every setting: environment, database URL, CORS origins, upload path/limit, OpenRouter credentials/model, Pinecone credentials/index, embedding model, retrieval defaults, and log level. Production mode fails at startup when required provider configuration is absent. Never commit `.env` or client documents.

## Test and quality commands

```bash
cd backend
ruff check .
ruff format --check .
pytest -q

cd ../frontend
npm run format:check
npm run lint
npm run build
```

Tests use fakes and require no real Pinecone/OpenRouter credentials. CI runs the same checks on pushes and pull requests.

## Docker workflow

Create `backend/.env` from the example, add provider credentials, then:

```bash
docker compose up --build
```

The frontend is served at `http://localhost:5173`, the API at `http://localhost:8000`, and named volumes preserve SQLite data/uploads. This is a local/demo setup, not a production topology.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | lightweight process liveness |
| GET | `/ready` | database, storage, vector, and LLM readiness |
| POST | `/documents/upload` | validate and synchronously index a document |
| GET | `/documents` | list documents |
| GET | `/documents/{id}` | document details |
| DELETE | `/documents/{id}` | delete vectors, metadata/chunks, and source file |
| POST | `/documents/chat` | ask a bounded question about one document |

Interactive OpenAPI documentation is at `/docs` while the API is running.

## Security and privacy

There is no authentication or user isolation. Do not expose v1.5 publicly or upload sensitive client data. Retrieved document excerpts are sent to OpenRouter; embeddings and join/isolation metadata are sent to Pinecone; original files remain on local disk. Review provider terms, retention, regional requirements, and data-processing obligations before any real-client use. Logs avoid secrets and full source content, but the prototype does not implement formal audit, retention, backup, encryption, or incident-response controls.

## Engineering decisions

- document-scoped vector filtering is mandatory at the interface boundary
- SQL owns text/metadata while Pinecone owns vector values
- deterministic vector IDs provide a stable join and cleanup mechanism
- ingestion uses rollback and compensating cleanup across systems
- no LLM call is made when retrieval evidence is empty or below threshold
- external integrations are narrow, injected in tests, and lazily initialized
- SQLite/local files keep the portfolio demo approachable; their scaling limits are explicit

## Roadmap

v2 focuses on real client-workspace workflow and asynchronous ingestion. v3 introduces multi-user SaaS foundations and production controls. Later possibilities include briefing generation, commitment/risk tracking, version change detection, and evaluation dashboards. None are claimed as implemented; see [the staged roadmap](docs/ROADMAP.md).

## License

MIT
