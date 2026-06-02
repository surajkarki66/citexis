import httpx

from app.config import Settings
from app.core.schemas.paper import AuthorSchema, PaperCreate
from app.services.ingestion.sources.base import PaperSource
from app.services.ingestion.sources.utils import (
    chunk_list,
    normalize_doi,
    openalex_short_id,
    reconstruct_abstract,
)

OPENALEX_API = "https://api.openalex.org/works"


class OpenAlexSource(PaperSource):
    def __init__(self, settings: Settings) -> None:
        self._max_citations = settings.ingestion_max_citations

    async def fetch(self, query: str, limit: int = 50) -> list[PaperCreate]:
        papers: list[PaperCreate] = []
        page = 1
        per_page = min(200, limit)

        async with httpx.AsyncClient(timeout=60.0) as client:
            while len(papers) < limit:
                response = await client.get(
                    OPENALEX_API,
                    params={
                        "search": query,
                        "per_page": min(per_page, limit - len(papers)),
                        "page": page,
                        "sort": "cited_by_count:desc",
                    },
                )
                response.raise_for_status()
                results = response.json().get("results", [])
                if not results:
                    break

                for work in results:
                    papers.append(await self._map_work(client, work))
                    if len(papers) >= limit:
                        break
                page += 1

        return papers

    async def fetch_by_doi(self, doi: str) -> PaperCreate | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{OPENALEX_API}/https://doi.org/{normalized}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return await self._map_work(client, response.json())

    async def _map_work(self, client: httpx.AsyncClient, work: dict) -> PaperCreate:
        title = work.get("title") or work.get("display_name") or "Untitled"
        authors = [
            AuthorSchema(
                name=a.get("author", {}).get("display_name") or a.get("raw_author_name", ""),
                affiliation=(
                    (a.get("institutions") or [{}])[0].get("display_name")
                    if a.get("institutions")
                    else None
                ),
                orcid=normalize_doi(a.get("author", {}).get("orcid")),
            )
            for a in work.get("authorships", [])
            if a.get("author", {}).get("display_name") or a.get("raw_author_name")
        ]

        location = work.get("primary_location") or {}
        source = location.get("source") or {}
        oa = work.get("open_access") or {}
        best_oa = work.get("best_oa_location") or {}

        tags: list[str] = []
        for keyword in work.get("keywords") or []:
            name = keyword.get("display_name")
            if name:
                tags.append(name)
        if not tags:
            for concept in (work.get("concepts") or [])[:5]:
                name = concept.get("display_name")
                if name:
                    tags.append(name)

        citations = await self._resolve_reference_dois(
            client, work.get("referenced_works") or []
        )

        return PaperCreate(
            doi=normalize_doi(work.get("doi")),
            title=title,
            authors=authors,
            abstract=reconstruct_abstract(work.get("abstract_inverted_index")),
            year=work.get("publication_year"),
            venue=source.get("display_name"),
            citations=citations,
            cited_by_count=int(work.get("cited_by_count") or 0),
            tags=tags,
            full_text_url=best_oa.get("pdf_url") or oa.get("oa_url") or location.get("pdf_url"),
        )

    async def _resolve_reference_dois(
        self,
        client: httpx.AsyncClient,
        referenced_works: list[str],
    ) -> list[str]:
        ref_ids = [openalex_short_id(ref) for ref in referenced_works[: self._max_citations]]
        dois: list[str] = []

        for chunk in chunk_list(ref_ids, 50):
            filter_value = "|".join(chunk)
            response = await client.get(
                OPENALEX_API,
                params={
                    "filter": f"openalex_id:{filter_value}",
                    "per_page": len(chunk),
                    "select": "doi",
                },
            )
            response.raise_for_status()
            for item in response.json().get("results", []):
                doi = normalize_doi(item.get("doi"))
                if doi:
                    dois.append(doi)

        return dois
