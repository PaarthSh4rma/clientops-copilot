import os

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(PINECONE_INDEX_NAME)


def upsert_document_chunks(
    document_id: str,
    chunks: list[dict],
    embeddings: list[list[float]],
):
    vectors = []

    for chunk, embedding in zip(chunks, embeddings):
        vectors.append(
            {
                "id": f"{document_id}-{chunk['chunk_index']}",
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                },
            }
        )

    index.upsert(vectors=vectors)


def semantic_search(
    query_embedding: list[float],
    top_k: int = 3,
):
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
    )

    return results.matches