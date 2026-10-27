"""Create or refresh the free Pinecone index used by the Vercel public demo."""

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from pinecone import Pinecone, ServerlessSpec
from sqlalchemy.orm import selectinload

from app.core.config import Settings
from app.db.session import build_session_factory
from app.integrations.embeddings import PineconeInferenceEmbeddings
from app.integrations.vector_store import PineconeVectorStore, VectorRecord
from app.models import Document
from app.services.demo_bootstrap import bootstrap_demo_metadata


def main() -> None:
    settings = Settings(
        embedding_provider="pinecone_inference",
        pinecone_index_name="clientops-recruiter-demo",
    )
    settings.validate_production_integrations()
    if not settings.pinecone_api_key or not settings.pinecone_index_name:
        raise RuntimeError("Pinecone configuration is required")

    samples = Path(__file__).resolve().parents[1] / "demo_documents"
    embeddings = PineconeInferenceEmbeddings(settings.pinecone_api_key, settings.pinecone_embedding_model)

    with TemporaryDirectory() as temp_dir:
        sessions = build_session_factory(Settings(database_url=f"sqlite:///{Path(temp_dir) / 'demo.db'}"))
        bootstrap_demo_metadata(sessions, samples)
        with sessions() as db:
            documents = db.query(Document).options(selectinload(Document.chunks)).all()
            passages = [chunk.text for document in documents for chunk in document.chunks]
            values = embeddings.embed(passages)
            offset = 0
            records = []
            for document in documents:
                for chunk, value in zip(
                    document.chunks,
                    values[offset : offset + len(document.chunks)],
                    strict=True,
                ):
                    records.append(
                        VectorRecord(
                            id=chunk.vector_id,
                            values=value,
                            metadata={"document_id": document.id, "chunk_id": chunk.id},
                        )
                    )
                offset += len(document.chunks)

    client = Pinecone(api_key=settings.pinecone_api_key)
    dimension = len(records[0].values)
    if settings.pinecone_index_name not in client.list_indexes().names():
        client.create_index(
            name=settings.pinecone_index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        for _ in range(30):
            if client.describe_index(settings.pinecone_index_name).status["ready"]:
                break
            time.sleep(2)
    description = client.describe_index(settings.pinecone_index_name)
    if description.dimension != dimension:
        raise RuntimeError(
            f"Index dimension is {description.dimension}; expected {dimension}. Use a new demo index name."
        )
    PineconeVectorStore(settings.pinecone_api_key, settings.pinecone_index_name).upsert(records)
    print(f"Prepared {len(records)} demo evidence chunks in {settings.pinecone_index_name}")


if __name__ == "__main__":
    main()
