from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import IngestionDep, PaperRepoDep, RecommendationsDep, SettingsDep
from app.core.schemas.paper import PaperCreate, PaperResponse
from app.core.schemas.recommendation import RecommendationResponse
from app.workers.tasks import (
    index_paper_task,
    ingest_doi_task,
    ingest_openalex_task,
    ingest_source_task,
)

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


@router.post("/import/openalex", status_code=status.HTTP_202_ACCEPTED)
async def import_openalex(
    query: str = "machine learning",
    limit: int = 50,
    enrich: bool = True,
) -> dict:
    task = ingest_openalex_task.delay(query, limit, enrich)
    return {"status": "accepted", "task_id": task.id, "source": "openalex"}


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


@router.post("/import/pdf/sync", response_model=dict)
async def import_pdf_sync(
    pipeline: IngestionDep,
    settings: SettingsDep,
    enrich: bool = True,
    files: list[UploadFile] = File(...),
) -> dict:
    """Synchronous PDF ingest: extract text/metadata and index each file."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload at least one PDF file",
        )
    if len(files) > settings.pdf_import_max_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {settings.pdf_import_max_files} PDF files per request",
        )

    payloads: list[tuple[str, bytes]] = []
    for upload in files:
        filename = upload.filename or "upload.pdf"
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only PDF files are supported: {filename}",
            )

        data = await upload.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Empty file: {filename}",
            )
        if len(data) > settings.pdf_import_max_bytes:
            max_mb = settings.pdf_import_max_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large (max {max_mb} MB): {filename}",
            )
        payloads.append((filename, data))

    result = await pipeline.ingest_from_pdfs(payloads, enrich=enrich)
    return {"status": "completed", **result}


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
