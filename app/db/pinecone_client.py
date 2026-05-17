from pinecone import Pinecone

from app.config import Settings

_pc: Pinecone | None = None


def get_pinecone(settings: Settings) -> Pinecone:
    global _pc
    if _pc is None:
        if not settings.pinecone_api_key:
            raise RuntimeError("PINECONE_API_KEY is required for vector operations")
        _pc = Pinecone(api_key=settings.pinecone_api_key)
    return _pc


def get_index(settings: Settings):
    return get_pinecone(settings).Index(settings.pinecone_index)
