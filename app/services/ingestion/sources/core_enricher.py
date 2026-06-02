import httpx

from app.config import Settings
from app.core.schemas.paper import PaperCreate
from app.services.ingestion.sources.utils import normalize_doi

CORE_SEARCH_API = "https://api.core.ac.uk/v3/search/works"


class CoreEnricher:
    """Optional OA PDF enrichment when OpenAlex/Crossref lack a full-text URL."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.core_api_key
        self._enabled = settings.ingestion_enrich_core and bool(self._api_key)

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def enrich(self, paper: PaperCreate) -> PaperCreate:
        if not self._enabled or paper.full_text_url:
            return paper

        doi = normalize_doi(paper.doi)
        if not doi:
            return paper

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                CORE_SEARCH_API,
                params={"q": f'doi:"{doi}"', "limit": 1},
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            if response.status_code != 200:
                return paper

            results = response.json().get("results") or []
            if not results:
                return paper

            work = results[0]
            download_url = work.get("downloadUrl")
            if not download_url:
                return paper

            return paper.model_copy(update={"full_text_url": download_url})
