from app.services.embeddings.base import EmbeddingService
from app.services.embeddings.local import LocalEmbeddingService


def get_embedding_service(model: str) -> EmbeddingService:
    return LocalEmbeddingService(model=model)


__all__ = ["EmbeddingService", "get_embedding_service"]
