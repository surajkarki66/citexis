from pydantic import BaseModel, Field


class ArxivPaperResult(BaseModel):
    arxiv_id: str | None = None
    title: str
    authors: list[str] = Field(default_factory=list)
    doi: str | None = None
    year: int | None = None


class ArxivSearchResponse(BaseModel):
    query: str
    arxiv_query: str
    total_results: int
    returned: int
    doi_count: int
    dois: list[str]
    papers: list[ArxivPaperResult]
