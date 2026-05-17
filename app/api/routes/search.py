from fastapi import APIRouter

from app.api.deps import SearchDep
from app.core.schemas.search import SearchRequest, SearchResponse

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def hybrid_search(body: SearchRequest, search: SearchDep) -> SearchResponse:
    return await search.search(body)
