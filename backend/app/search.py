import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def rank_chunks(
    query_embedding: list[float],
    chunks: list[dict],
    chunk_embeddings: list[list[float]],
    top_k: int = 3,
) -> list[dict]:
    scored_chunks = []

    for chunk, embedding in zip(chunks, chunk_embeddings):
        score = cosine_similarity(query_embedding, embedding)
        scored_chunks.append({
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
            "score": round(score, 4),
            "character_count": chunk["character_count"],
        })

    return sorted(scored_chunks, key=lambda item: item["score"], reverse=True)[:top_k]