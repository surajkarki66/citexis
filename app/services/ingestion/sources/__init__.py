from app.services.ingestion.sources.base import PaperSource
from app.services.ingestion.sources.core_enricher import CoreEnricher
from app.services.ingestion.sources.crossref import CrossrefDoiSource
from app.services.ingestion.sources.openalex import OpenAlexSource

__all__ = [
    "PaperSource",
    "OpenAlexSource",
    "CrossrefDoiSource",
    "CoreEnricher",
]
