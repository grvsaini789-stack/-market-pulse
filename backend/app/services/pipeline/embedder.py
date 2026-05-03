from __future__ import annotations
from functools import lru_cache
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed(texts: list[str]) -> list[list[float]]:
    """Return 384-dim embeddings for a list of strings."""
    if not texts:
        return []
    model = _get_model()
    vecs = model.encode(texts, batch_size=64, show_progress_bar=False)
    return [v.tolist() for v in vecs]


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
