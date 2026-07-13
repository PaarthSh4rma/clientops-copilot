# Product Audit — v1 Prototype

## Executive summary

The original application was a functional single-document RAG demo: it accepted TXT/PDF/DOCX files, extracted and chunked text, generated local embeddings, wrote vectors to Pinecone, and used OpenRouter for an answer. Its visual foundation was coherent. It was not yet a trustworthy product foundation because retrieval was not document-scoped, persistence had conflicting ownership, provider clients were created during import, failures leaked files/partial data, and the UI asserted readiness without checking it.

The recommended positioning is: **a portfolio project and evolving, single-workspace client knowledge prototype for source-grounded questions across client material**. It must not be described as production-ready, multi-user, hallucination-free, or enterprise software.

## What was already well implemented

- `backend/app/extractors.py` supported the promised three formats with appropriate libraries.
- `backend/main.py::chunk_text` used bounded overlap and a sensible recursive splitter.
- `backend/app/embeddings.py` normalized SentenceTransformer embeddings and cached the model.
- `backend/app/llm.py::generate_grounded_answer` used a low temperature and asked the model to rely on context.
- `frontend/src/components/*` provided a consistent responsive visual language, loading indicators, and a keyboard-native question form.

## Findings

### Critical

1. **Cross-document retrieval.** `backend/app/vectorstore.py::semantic_search` queried the entire Pinecone index without a `document_id` filter. `backend/main.py::chat_with_document` then labelled every match with the requested document filename, so unrelated text could be presented as a citation. v1.5 fixes this through a required `VectorStore.search(document_id=...)` contract and Pinecone metadata filter.
2. **Conflicting data ownership.** Embeddings were stored as stringified Python lists in `DocumentChunk.embedding` while Pinecone was also used as the retrieval source. The database and vector index could drift. v1.5 removes embedding arrays from the relational model: SQL owns document/chunk metadata and vector IDs; Pinecone owns vector values.

### High

- Uploads were written before extraction and never removed on extraction, empty-text, embedding, vector, or database failure (`backend/main.py::upload_document`).
- Vector upsert occurred before database persistence with no compensating delete, permitting orphan vectors.
- database sessions were manually created; 404 and provider paths could skip `close()`.
- Pinecone and OpenRouter clients were created at module import (`vectorstore.py`, `llm.py`), making startup and tests dependent on secrets/network behavior.
- all LLM exceptions became a success-looking fallback, concealing provider failure.
- TXT decoding, encrypted/malformed PDF, invalid DOCX, MIME mismatch, and upload size were not handled consistently.
- no list/detail/delete lifecycle existed; local files and vectors had no supported cleanup path.
- no migrations existed; `create_all()` ran during import and could not evolve an existing schema.

### Medium

- PDF page boundaries and DOCX paragraph locations were discarded, weakening citations.
- `top_k` had no bounds and retrieval had no minimum score.
- the LLM prompt did not explicitly treat uploaded instructions as untrusted prompt-injection content.
- CORS allowed every origin with credentials.
- readiness was not measured; `Header.tsx` hard-coded “Pinecone RAG Engine Online.”
- the frontend supported only the most recent upload and had no real empty library, selection, deletion, or provider-failure state.
- dependency management was an accidental full `pip freeze`; tests and CI were absent.

### Later

- duplicate checksums are recorded but duplicate-policy UX is intentionally deferred.
- extraction remains synchronous and does not provide OCR, tables, or rich structure.
- local source files and SQLite are appropriate for a demo, not horizontally scaled deployment.
- retrieval evaluation, reranking, hybrid search, observability, authentication, and tenant isolation remain future work.

## Security and privacy

Documents are sent in retrieved excerpts to OpenRouter and vector values/metadata identifiers are sent to Pinecone. Local source files remain unencrypted on disk. There is no authentication or tenant boundary. Do not expose this version to untrusted users or sensitive client material. Secrets belong only in environment variables; logs must not include keys or full document content.

## Deployment blockers

For any public production deployment: authentication/authorization, tenant isolation, managed relational/object storage, durable jobs, rate/usage limits, retention controls, encryption/key management, backups, monitoring, and a formal provider/privacy review are required. Docker support in v1.5 is a local/demo convenience, not production certification.

## Prioritised recommendation status

- **Critical:** document-scoped retrieval and deliberate data ownership — implemented in v1.5.
- **High:** transactional/compensating ingestion, lifecycle APIs, migrations, stable errors, typed configuration — implemented in v1.5.
- **Medium:** source locations, readiness, honest document-library UX, CI/tooling — implemented to a focused v1.5 level.
- **Later:** asynchronous ingestion, richer source viewer, multi-workspace/product workflow, production SaaS controls — roadmap only.
