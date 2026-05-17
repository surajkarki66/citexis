from elasticsearch import AsyncElasticsearch

from app.config import Settings
from app.core.schemas.search import SearchFilters


class KeywordSearchService:
    def __init__(self, settings: Settings, client: AsyncElasticsearch) -> None:
        self._settings = settings
        self._client = client

    async def search(self, query: str, filters: SearchFilters, top_k: int = 50) -> list[str]:
        must = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "abstract^1.5"],
                    "type": "best_fields",
                }
            }
        ]
        filter_clauses = []
        if filters.year_min or filters.year_max:
            year_range: dict = {}
            if filters.year_min:
                year_range["gte"] = filters.year_min
            if filters.year_max:
                year_range["lte"] = filters.year_max
            filter_clauses.append({"range": {"year": year_range}})
        if filters.tags:
            filter_clauses.append({"terms": {"tags": filters.tags}})
        if filters.venue:
            filter_clauses.append({"term": {"venue": filters.venue}})

        body = {
            "size": top_k,
            "query": {
                "function_score": {
                    "query": {"bool": {"must": must, "filter": filter_clauses}},
                    "field_value_factor": {
                        "field": "citation_count",
                        "modifier": "log1p",
                        "factor": 0.1,
                    },
                    "boost_mode": "sum",
                }
            },
        }
        response = await self._client.search(index=self._settings.elasticsearch_index, body=body)
        return [hit["_source"]["paper_id"] for hit in response["hits"]["hits"]]
