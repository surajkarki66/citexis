from abc import ABC, abstractmethod


class Reranker(ABC):
    @abstractmethod
    def rerank(self, query: str, documents: list[str], top_n: int) -> list[str]:
        """Reorder document texts by relevance to query."""


class PassthroughReranker(Reranker):
    def rerank(self, query: str, documents: list[str], top_n: int) -> list[str]:
        return documents[:top_n]


class CohereReranker(Reranker):
    """Phase 2+: wire Cohere Rerank API."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def rerank(self, query: str, documents: list[str], top_n: int) -> list[str]:
        raise NotImplementedError("Cohere reranker — implement in Phase 2")
