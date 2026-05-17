from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_paper(self, title: str, abstract: str, keywords: list[str] | None = None) -> list[float]:
        parts = [title.strip(), abstract.strip()]
        if keywords:
            parts.append("Keywords: " + ", ".join(k.strip() for k in keywords if k.strip()))
        return self.embed_text("\n\n".join(p for p in parts if p))
