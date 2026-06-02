from app.config import Settings
from app.services.ingestion.sources.base import PaperSource
from app.services.ingestion.sources.crossref import CrossrefDoiSource
from app.services.ingestion.sources.openalex import OpenAlexSource

SOURCE_NAMES = ("openalex", "crossref")


def get_paper_source(name: str, settings: Settings) -> PaperSource:
    if name == "openalex":
        return OpenAlexSource(settings)
    if name == "crossref":
        return CrossrefDoiSource()
    raise ValueError(f"Unknown source '{name}'. Choose from: {', '.join(SOURCE_NAMES)}")
