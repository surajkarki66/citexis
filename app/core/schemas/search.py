from pydantic import BaseModel, Field

from app.core.schemas.paper import PaperSummary


class SearchFilters(BaseModel):
    year_min: int | None = None
    year_max: int | None = None
    tags: list[str] = Field(default_factory=list)
    venue: str | None = None


class SearchRequest(BaseModel):
    query: str
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = 10


class SearchResult(BaseModel):
    paper: PaperSummary
    score: float
    source: str  # elasticsearch | pinecone | hybrid


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
