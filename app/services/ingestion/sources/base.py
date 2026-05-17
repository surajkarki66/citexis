from abc import ABC, abstractmethod

from app.core.schemas.paper import PaperCreate


class PaperSource(ABC):
    @abstractmethod
    async def fetch(self, query: str, limit: int) -> list[PaperCreate]:
        """Fetch raw papers from an external source."""
