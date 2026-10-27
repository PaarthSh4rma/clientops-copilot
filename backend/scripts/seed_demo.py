"""Index the bundled non-sensitive demo documents through the real ingestion pipeline."""

from pathlib import Path

from app.core.config import get_settings
from app.db.session import build_session_factory
from app.integrations.embeddings import SentenceTransformerEmbeddings
from app.integrations.file_storage import LocalFileStorage
from app.integrations.vector_store import PineconeVectorStore
from app.services.ingestion import IngestionService


def main() -> None:
    settings = get_settings()
    settings.validate_production_integrations()
    if not settings.pinecone_api_key or not settings.pinecone_index_name:
        raise RuntimeError("Pinecone configuration is required to seed the real retrieval pipeline")

    samples = Path(__file__).resolve().parents[1] / "demo_documents"
    storage = LocalFileStorage(settings.upload_directory)
    embeddings = SentenceTransformerEmbeddings(settings.embedding_model)
    vectors = PineconeVectorStore(settings.pinecone_api_key, settings.pinecone_index_name)

    with build_session_factory(settings)() as db:
        service = IngestionService(db, storage, embeddings, vectors, settings.max_upload_size_bytes)
        for path in sorted(samples.glob("*.txt")):
            try:
                document, _ = service.ingest(path.name, "text/plain", path.read_bytes())
                print(f"Indexed {document.original_filename} ({document.chunk_count} chunks)")
            except ValueError as exc:
                if "already indexed" in str(exc):
                    print(f"Skipped {path.name}: already indexed")
                else:
                    raise


if __name__ == "__main__":
    main()
