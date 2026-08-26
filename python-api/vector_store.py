"""
Etapa de ARMAZENAMENTO/RECUPERAÇÃO VETORIAL: guarda os embeddings dos
chunks no Qdrant e permite buscar, para uma pergunta, os chunks mais
semanticamente parecidos (busca por similaridade de vetores).
"""

import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documentos_curso")

_client = QdrantClient(url=QDRANT_URL)


def ensure_collection(vector_size: int) -> None:
    existing = [c.name for c in _client.get_collections().collections]
    if QDRANT_COLLECTION not in existing:
        _client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_chunks(chunks: list[str], embeddings: list[list[float]], source: str) -> int:
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"text": chunk, "source": source, "chunk_index": i},
        )
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    _client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return len(points)


def search(query_embedding: list[float], top_k: int = 4) -> list[dict]:
    results = _client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_embedding,
        limit=top_k,
    )
    return [
        {
            "text": r.payload.get("text", ""),
            "source": r.payload.get("source", ""),
            "score": r.score,
        }
        for r in results
    ]


def collection_info() -> dict:
    try:
        info = _client.get_collection(QDRANT_COLLECTION)
        return {
            "collection": QDRANT_COLLECTION,
            "points_count": info.points_count,
            "status": str(info.status),
        }
    except Exception:
        return {"collection": QDRANT_COLLECTION, "points_count": 0, "status": "not_created"}
