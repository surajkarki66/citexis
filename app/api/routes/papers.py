import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import IngestionDep, PaperRepoDep, RecommendationsDep, SettingsDep
from app.core.schemas.arxiv import ArxivSearchResponse
from app.core.schemas.doi_import import DoiBulkImportRequest
from app.core.schemas.paper import PaperCreate, PaperResponse
from app.core.schemas.recommendation import RecommendationResponse
from app.core.doi import normalize_doi
from app.services.ingestion.json_import import JsonImportError, parse_papers_json
from app.services.ingestion.sources.arxiv import ArxivSource
from app.workers.tasks import (
    index_paper_task,
    ingest_doi_task,
    ingest_dois_bulk_task,
    ingest_json_bulk_task,
    ingest_openalex_task,
    ingest_source_task,
)

router = APIRouter()


@router.get("/stats")
async def paper_stats(papers: PaperRepoDep) -> dict:
    """Corpus size for the home page and dashboards."""
    total = await papers.count_all()
    return {"total_papers": total}


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
        {**doc, "recommendations": [item.model_dump() for item in related.items]},
    )


@router.get("/{paper_id}/related", response_model=RecommendationResponse)
async def get_related(paper_id: str, recommendations: RecommendationsDep) -> RecommendationResponse:
    return await recommendations.get_related(paper_id)


@router.delete("/{paper_id}", response_model=dict)
async def delete_paper(paper_id: str, pipeline: IngestionDep) -> dict:
    deleted = await pipeline.delete_paper(paper_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return {"status": "deleted", "paper_id": paper_id}


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_paper(body: PaperCreate) -> dict:
    """Queue async indexing. Returns task id."""
    task = index_paper_task.delay(body.model_dump())
    return {"status": "accepted", "task_id": task.id}


@router.post("/sync", response_model=dict)
async def ingest_paper_sync(
    body: PaperCreate,
    pipeline: IngestionDep,
    enrich: bool = True,
) -> dict:
    """Synchronous manual ingest (blocks until MongoDB + indexes complete)."""
    label = body.doi or body.title
    try:
        paper_id = await pipeline.ingest_one(body, enrich=enrich)
    except Exception as exc:
        return {
            "status": "completed",
            "imported": 0,
            "skipped": 0,
            "failed": 1,
            "paper_ids": [],
            "skipped_items": [],
            "failed_items": [label],
            "failed_reasons": [f"{label}: {exc.__class__.__name__}: {exc}"],
        }

    if paper_id:
        return {
            "status": "completed",
            "imported": 1,
            "skipped": 0,
            "failed": 0,
            "paper_ids": [paper_id],
            "skipped_items": [],
            "failed_items": [],
            "failed_reasons": [],
        }

    return {
        "status": "completed",
        "imported": 0,
        "skipped": 1,
        "failed": 0,
        "paper_ids": [],
        "skipped_items": [label],
        "failed_items": [],
        "failed_reasons": [],
    }


@router.post("/import/json", status_code=status.HTTP_202_ACCEPTED)
async def import_json_bulk(
    settings: SettingsDep,
    file: UploadFile = File(...),
) -> dict:
    """Queue bulk paper import from a complete JSON file (no CORE enrichment)."""
    filename = file.filename or "upload.json"
    if not filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only JSON files are supported: {filename}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Empty file: {filename}",
        )
    if len(data) > settings.json_import_max_bytes:
        max_kb = settings.json_import_max_bytes // 1024
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large (max {max_kb} KB): {filename}",
        )

    try:
        papers = parse_papers_json(data)
    except JsonImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if len(papers) > settings.json_import_max_papers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.json_import_max_papers} papers per JSON import",
        )

    task = ingest_json_bulk_task.delay(
        [paper.model_dump(mode="json") for paper in papers],
        False,
    )
    return {
        "status": "accepted",
        "task_id": task.id,
        "source": "json",
        "queued": len(papers),
    }


@router.post("/import/openalex", status_code=status.HTTP_202_ACCEPTED)
async def import_openalex(
    query: str = "machine learning",
    limit: int = 50,
    enrich: bool = True,
) -> dict:
    limit = max(1, min(limit, 50))
    task = ingest_openalex_task.delay(query, limit, enrich)
    return {
        "status": "accepted",
        "task_id": task.id,
        "source": "openalex",
        "queued": limit,
    }


@router.post("/import/doi/bulk", status_code=status.HTTP_202_ACCEPTED)
async def import_dois_bulk(
    settings: SettingsDep,
    body: DoiBulkImportRequest,
) -> dict:
    """Queue bulk DOI import (Crossref + optional CORE enrichment)."""
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in body.dois:
        doi = normalize_doi(raw) or raw.strip()
        if not doi or doi in seen:
            continue
        seen.add(doi)
        normalized.append(doi)

    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid DOIs provided",
        )

    if len(normalized) > settings.json_import_max_papers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.json_import_max_papers} DOIs per bulk import",
        )

    task = ingest_dois_bulk_task.delay(normalized, body.enrich)
    return {
        "status": "accepted",
        "task_id": task.id,
        "source": "crossref",
        "queued": len(normalized),
    }


@router.post("/import/doi", status_code=status.HTTP_202_ACCEPTED)
async def import_doi(doi: str, enrich: bool = True) -> dict:
    task = ingest_doi_task.delay(doi, enrich)
    return {"status": "accepted", "task_id": task.id, "source": "crossref"}


@router.post("/import/{source}", status_code=status.HTTP_202_ACCEPTED)
async def import_from_source(
    source: str,
    query: str = "machine learning",
    limit: int = 50,
    enrich: bool = True,
) -> dict:
    """Generic import: openalex | crossref (query = DOI for crossref)."""
    if source not in ("openalex", "crossref"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source must be openalex or crossref",
        )
    task = ingest_source_task.delay(source, query, limit, enrich)
    return {"status": "accepted", "task_id": task.id, "source": source}


@router.post("/import/doi/sync", response_model=dict)
async def import_doi_sync(
    doi: str,
    pipeline: IngestionDep,
    enrich: bool = True,
) -> dict:
    """Synchronous DOI ingest for testing (blocks until MongoDB + indexes complete)."""
    from app.services.ingestion.sources.crossref import CrossrefDoiSource

    source = CrossrefDoiSource()
    result = await pipeline.ingest_from_source(source, doi, 1, enrich=enrich)
    return {"status": "completed", **result}


@router.get("/import/arxiv/search", response_model=ArxivSearchResponse)
async def search_arxiv(
    query: str,
    limit: int = 10,
) -> ArxivSearchResponse:
    """Search arXiv and extract DOIs from matching papers."""
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query is required",
        )

    source = ArxivSource()
    try:
        result = await source.search(query, limit)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach arXiv API: {exc.__class__.__name__}: {exc}",
        ) from exc

    return ArxivSearchResponse.model_validate(result)


@router.post("/import/openalex/sync", response_model=dict)
async def import_openalex_sync(
    settings: SettingsDep,
    pipeline: IngestionDep,
    query: str = "machine learning",
    limit: int = 10,
    enrich: bool = True,
) -> dict:
    """Synchronous OpenAlex search ingest (blocks until MongoDB + indexes complete)."""
    from app.services.ingestion.sources.openalex import OpenAlexSource

    limit = max(1, min(limit, 50))
    source = OpenAlexSource(settings)
    result = await pipeline.ingest_from_source(source, query, limit, enrich=enrich)
    return {"status": "completed", **result}
