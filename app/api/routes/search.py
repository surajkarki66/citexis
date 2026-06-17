from fastapi import APIRouter

from app.api.deps import KeywordSearchDep, PaperRepoDep, SearchDep, SemanticSearchDep
from app.core.schemas.search import SearchRequest, SearchResponse, SearchResult

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def hybrid_search(body: SearchRequest, search: SearchDep) -> SearchResponse:
    return await search.search(body)


async def _build_search_response(
    *,
    query: str,
    results: list[tuple[str, float]],
    paper_repo,
    source: str,
    limit: int,
) -> SearchResponse:
    paper_ids = [paper_id for paper_id, _ in results[:limit]]
    docs = await paper_repo.get_many_by_ids(paper_ids)
    doc_map = {str(doc["_id"]): doc for doc in docs}

    items: list[SearchResult] = []
    for paper_id, score in results[:limit]:
        doc = doc_map.get(paper_id)
        if not doc:
            continue
        items.append(
            SearchResult(
                paper=paper_repo.to_summary(doc),
                score=score,
                source=source,
            )
        )

    return SearchResponse(query=query, results=items, total=len(items))


@router.post("/search/semantic", response_model=SearchResponse)
async def semantic_search(
    body: SearchRequest,
    search: SemanticSearchDep,
    paper_repo: PaperRepoDep,
) -> SearchResponse:
    results = await search.search(body.query, body.filters, body.top_k)
    
    paper_ids = [paper_id for paper_id, _ in results[:body.top_k]]
    docs = await paper_repo.get_many_by_ids(paper_ids)
    doc_map = {str(doc["_id"]): doc for doc in docs}

    items: list[SearchResult] = []
    for paper_id, score in results[:body.top_k]:
        doc = doc_map.get(paper_id)
        if not doc:
            continue
        items.append(
            SearchResult(
                paper=paper_repo.to_summary(doc),
                score=score,
                source="pinecone",
            )
        )

    return SearchResponse(query=body.query, results=items, total=len(items))


@router.post("/search/keyword", response_model=SearchResponse)
async def keyword_search(
    body: SearchRequest,
    search: KeywordSearchDep,
    paper_repo: PaperRepoDep,
) -> SearchResponse:
    results = await search.search(body.query, body.filters, body.top_k)
    paper_ids = [paper_id for paper_id, _ in results[:body.top_k]]
    docs = await paper_repo.get_many_by_ids(paper_ids)
    doc_map = {str(doc["_id"]): doc for doc in docs}

    items: list[SearchResult] = []
    for paper_id, score in results[:body.top_k]:
        doc = doc_map.get(paper_id)
        if not doc:
            continue
        items.append(
            SearchResult(
                paper=paper_repo.to_summary(doc),
                score=score,
                source="elasticsearch",
            )
        )

    return SearchResponse(query=body.query, results=items, total=len(items))
