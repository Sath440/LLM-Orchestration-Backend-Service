from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from api.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_texts(texts: List[str]) -> List[list[float]]:
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embedding_dimension() -> int:
    return settings.embedding_dim
