from elasticsearch import AsyncElasticsearch

from app.config import Settings


class ElasticsearchIndexer:
    def __init__(self, settings: Settings, client: AsyncElasticsearch) -> None:
        self._index = settings.elasticsearch_index
        self._client = client

    async def index_paper(self, paper_id: str, doc: dict) -> None:
        body = {
            "paper_id": paper_id,
            "title": doc.get("title", ""),
            "abstract": doc.get("abstract", ""),
            "authors": [a.get("name", "") for a in doc.get("authors", [])],
            "year": doc.get("year"),
            "venue": doc.get("venue"),
            "tags": doc.get("tags", []),
            "citation_count": int(doc.get("cited_by_count") or 0),
        }
        await self._client.index(index=self._index, id=paper_id, document=body)

    async def delete_paper(self, paper_id: str) -> None:
        await self._client.delete(index=self._index, id=paper_id, ignore=[404])
