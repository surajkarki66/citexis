import asyncio
from typing import Any

from app.config import Settings
from app.core.schemas.search import SearchFilters

SEARCH_RETURN_FIELDS = ("title", "paper_id", "year", "venue")
MAX_RERANK_QUERY_CHARS = 4_000


def _prepare_query(query: str, rerank_enabled: bool) -> str:
    if not rerank_enabled or len(query) <= MAX_RERANK_QUERY_CHARS:
        return query
    return query[:MAX_RERANK_QUERY_CHARS]


def _hit_id(hit: Any) -> str:
    if hasattr(hit, "id"):
        return str(hit.id)
    return str(hit["id"])


def _hit_score(hit: Any) -> float:
    if hasattr(hit, "score"):
        return float(hit.score or 0.0)
    return float(hit.get("score") or 0.0)


def _response_hits(response: Any) -> list:
    if hasattr(response, "result"):
        return list(response.result.hits or [])
    return list(response.get("result", {}).get("hits", []))


def _build_filter(filters: SearchFilters) -> dict | None:
    conditions = []
    if filters.year_min is not None:
        conditions.append({"year": {"$gte": filters.year_min}})
    if filters.year_max is not None:
        conditions.append({"year": {"$lte": filters.year_max}})
    if filters.venue:
        conditions.append({"venue": {"$eq": filters.venue}})
    if filters.tags:
        conditions.append({"tags": {"$in": filters.tags}})
    if not conditions:
        return None
    return {"$and": conditions} if len(conditions) > 1 else conditions[0]


def search_index_sync(
    index,
    settings: Settings,
    *,
    query: str,
    filters: SearchFilters,
    top_k: int,
) -> list[tuple[str, float]]:
    """Search + rerank in one Pinecone call."""
    text_field = settings.pinecone_text_field
    fields = [text_field, *SEARCH_RETURN_FIELDS]
    rerank_enabled = settings.pinecone_rerank_enabled
    query = _prepare_query(query, rerank_enabled)

    kwargs: dict[str, Any] = {
        "inputs": {"text": query},
        "namespace": settings.pinecone_namespace,
        "top_k": top_k,
        "fields": fields,
    }

    pinecone_filter = _build_filter(filters)
    if pinecone_filter:
        kwargs["filter"] = pinecone_filter

    if rerank_enabled:
        kwargs["rerank"] = {
            "model": settings.pinecone_rerank_model,
            "top_n": top_k,
            "rank_fields": [text_field],
            "parameters": {"truncate": "END"},
        }

    response = index.search(**kwargs)
    return [(_hit_id(h), _hit_score(h)) for h in _response_hits(response)]


async def search_index(
    index,
    settings: Settings,
    *,
    query: str,
    filters: SearchFilters,
    top_k: int,
) -> list[tuple[str, float]]:
    return await asyncio.to_thread(
        search_index_sync,
        index,
        settings,
        query=query,
        filters=filters,
        top_k=top_k,
    )
