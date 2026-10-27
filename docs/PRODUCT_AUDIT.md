# Product Audit — v1.6 Portfolio Product

## Audit outcome

The v1.5 backend was already a technically careful RAG foundation: it enforced document-scoped retrieval, established storage ownership, added compensating cleanup, preserved source locations, separated answer outcomes, and introduced migrations/tests. Its main weakness was no longer core RAG correctness; it was the gap between those guarantees and the experience a recruiter or operator could understand in a short session.

v1.6 closes that product gap without turning the application into a multi-tenant SaaS platform or replacing its retrieval architecture.

## Weak or incomplete before this pass

### Product and frontend

- The two-card layout read as an upload/chat prototype rather than a working operational tool.
- Only the latest answer remained visible; there was no per-document browser-session history.
- Citations were nested below the answer instead of being a first-class inspection workflow.
- Raw similarity numbers had no human-readable interpretation.
- Suggested tasks were copy only, not reusable transparent prompt actions.
- Delete used a browser-native confirmation and lifecycle errors were generic.
- Duplicate checksums were stored but not enforced or surfaced.
- Public demonstration would have exposed arbitrary upload/delete and uncontrolled provider usage.
- Vite starter CSS/assets and dead UI components remained in the repository.
- No deterministic frontend interaction tests existed.

### Backend and operations

- OpenRouter used SDK defaults rather than an explicit bounded timeout/retry policy.
- CORS enabled credentials despite having no cookie/authentication workflow.
- Readiness did not expose mode/capability information to the frontend.
- No deterministic retrieval-quality fixture asserted expected chunk relevance and threshold abstention.
- Deployment documentation did not define a safe single-instance public demo topology.

## What changed

- Introduced a responsive library/workspace/evidence information architecture.
- Added five visible workflow actions that select the chosen document's source passages directly, avoiding false retrieval misses for generic prompts.
- Preserved a question/answer timeline per document in browser memory only.
- Made supported, insufficient-evidence, and provider-failure outcomes visually and semantically distinct.
- Added an evidence inspector with location, preview, qualitative relevance, exact cosine similarity, and citation switching.
- Added inline destructive confirmation, long-filename handling, stable loading shells, and actionable empty/offline states.
- Enforced checksum duplicate detection before file/vector writes and returned the existing document ID for selection.
- Added `DEMO_MODE`, protected shared samples, capability flags, synthetic documents, a real-pipeline seeder, per-session soft limits, and bounded sample-answer caching.
- Enabled temporary TXT/PDF/DOCX uploads in the public deployment without paid storage; uploaded text and embeddings stay in browser memory between requests and are not added to shared SQL, Pinecone vector storage, or the answer cache.
- Added source-backed follow-up context, safe Markdown rendering, and retained evidence when a later question has insufficient support.
- Added explicit OpenRouter timeout and one retry; removed unnecessary credentialed CORS.
- Added deterministic retrieval evaluation and focused UI interaction tests.
- Removed obsolete starter assets, CSS, and unused card/button/status components.

## Guarantees retained

- Vector search and deletion require a document ID filter.
- For durable documents, SQL owns text/metadata/vector IDs, Pinecone owns vectors, and storage owns bytes. Browser-session uploads carry their own bounded text/vector state.
- Specific questions pass a relevance gate; document-wide workflows and contextual follow-ups select explicit source passages without fabricating similarity scores.
- Insufficient evidence is not presented as success or provider failure.
- Uploaded text remains untrusted prompt content.
- Failed ingestion rolls back SQL and compensates vectors/files.
- Tests remain credential-free.

## Audit findings intentionally not expanded into architecture work

- Synchronous ingestion is acceptable for the current document limits and demo scope.
- Deletion across SQL/Pinecone/files cannot be a true distributed transaction. Interrupted cleanup remains visible as a failed document for explicit retry rather than false success.
- A richer original-file renderer was not added: the evidence drawer truthfully presents the exact retrieved passage and location.
- PostgreSQL, object storage, jobs, authentication, and tenancy are not required for a controlled single-instance portfolio demo.

## Security and privacy position

Demo mode reduces public exposure; it does not create an authorization boundary. Only bundled synthetic documents should be seeded. Host-level request limits, secret management, HTTPS, budget alerts, persistent-disk backups, and provider privacy review remain deployment responsibilities. The project does not claim production readiness, enterprise security, or hallucination-free answers.
