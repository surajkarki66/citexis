import httpx

from app.core.schemas.paper import AuthorSchema, PaperCreate
from app.services.ingestion.sources.base import PaperSource
from app.services.ingestion.sources.utils import normalize_doi, reconstruct_abstract, strip_html

CROSSREF_API = "https://api.crossref.org/works"
OPENALEX_API = "https://api.openalex.org/works"


class CrossrefDoiSource(PaperSource):
    """Resolve a single work by DOI via Crossref."""

    @staticmethod
    def _headers() -> dict[str, str]:
        return {
            "Accept": "application/json",
            "User-Agent": "Citexis/1.0",
        }

    async def fetch(self, query: str, limit: int = 1) -> list[PaperCreate]:
        paper = await self.fetch_by_doi(query)
        return [paper] if paper else []

    async def fetch_by_doi(self, doi: str) -> PaperCreate | None:
        normalized = normalize_doi(doi)
        if not normalized:
            return None

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{CROSSREF_API}/{normalized}",
                headers=self._headers(),
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            paper = self._map_work(response.json()["message"])
            if not paper.abstract:
                fallback_abstract = await self._fetch_openalex_abstract(client, normalized)
                if fallback_abstract:
                    paper = paper.model_copy(update={"abstract": fallback_abstract})
            return paper

    async def _fetch_openalex_abstract(self, client: httpx.AsyncClient, doi: str) -> str:
        response = await client.get(f"{OPENALEX_API}/https://doi.org/{doi}")
        if response.status_code == 404:
            return ""
        response.raise_for_status()
        work = response.json()
        return reconstruct_abstract(work.get("abstract_inverted_index"))

    def _map_work(self, work: dict) -> PaperCreate:
        title_field = work.get("title") or []
        title = title_field[0] if title_field else "Untitled"

        authors = []
        for author in work.get("author") or []:
            given = author.get("given", "")
            family = author.get("family", "")
            name = f"{given} {family}".strip()
            affiliation = None
            affiliations = author.get("affiliation") or []
            if affiliations:
                affiliation = affiliations[0].get("name")
            if name:
                authors.append(AuthorSchema(name=name, affiliation=affiliation))

        year = None
        for date_key in ("issued", "published-print", "published-online", "created"):
            date_parts = (work.get(date_key) or {}).get("date-parts")
            if date_parts and date_parts[0]:
                year = date_parts[0][0]
                break

        venue_field = work.get("container-title") or []
        venue = venue_field[0] if venue_field else None

        pdf_url = None
        for link in work.get("link") or []:
            if link.get("content-type") == "application/pdf" and link.get("URL"):
                pdf_url = link["URL"]
                break

        citations: list[str] = []
        for ref in work.get("reference") or []:
            ref_doi = normalize_doi(ref.get("DOI"))
            if ref_doi:
                citations.append(ref_doi)

        return PaperCreate(
            doi=normalize_doi(work.get("DOI")),
            title=title,
            authors=authors,
            abstract=strip_html(work.get("abstract") or ""),
            year=year,
            venue=venue,
            citations=citations,
            cited_by_count=int(work.get("is-referenced-by-count") or 0),
            tags=[],
            full_text_url=pdf_url or work.get("URL"),
        )
