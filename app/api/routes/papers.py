from fastapi import APIRouter, HTTPException, status

from app.api.deps import IngestionDep, PaperRepoDep, RecommendationsDep
from app.core.schemas.paper import PaperCreate, PaperResponse
from app.core.schemas.recommendation import RecommendationResponse
from app.workers.tasks import index_paper_task, ingest_arxiv_task

router = APIRouter()


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    papers: PaperRepoDep,
    recommendations: RecommendationsDep,
) -> PaperResponse:
    doc = await papers.get_by_id(paper_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    related = await recommendations.get_related(paper_id, limit=5)
    doc = {**doc, "_id": str(doc["_id"])}
    return PaperResponse.model_validate(
        {**doc, "recommendations": [item.paper for item in related.items]},
    )


@router.get("/{paper_id}/related", response_model=RecommendationResponse)
async def get_related(paper_id: str, recommendations: RecommendationsDep) -> RecommendationResponse:
    return await recommendations.get_related(paper_id)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_paper(body: PaperCreate) -> dict:
    """Queue async indexing. Returns task id."""
    task = index_paper_task.delay(body.model_dump())
    return {"status": "accepted", "task_id": task.id}


@router.post("/import/arxiv", status_code=status.HTTP_202_ACCEPTED)
async def import_arxiv(query: str = "machine learning", limit: int = 50) -> dict:
    """Bulk import from arXiv (Phase 1)."""
    task = ingest_arxiv_task.delay(query, limit)
    return {"status": "accepted", "task_id": task.id}
