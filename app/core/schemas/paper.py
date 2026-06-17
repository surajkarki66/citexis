from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import EmbeddingStatus, RecommendationReason


class AuthorSchema(BaseModel):
    name: str
    affiliation: str | None = None
    orcid: str | None = None


class PaperBase(BaseModel):
    doi: str | None = None
    title: str
    authors: list[AuthorSchema] = Field(default_factory=list)
    abstract: str = ""
    year: int | None = None
    venue: str | None = None
    citations: list[str] = Field(default_factory=list)
    cited_by_count: int = 0
    tags: list[str] = Field(
        default_factory=list,
        description="Topic keywords stored with paper metadata",
    )
    full_text_url: str | None = None


class PaperCreate(PaperBase):
    """Payload for manual ingest or normalized external metadata."""


class PaperInDB(PaperBase):
    id: str = Field(alias="_id")
    embedding_status: EmbeddingStatus = EmbeddingStatus.PENDING
    pinecone_id: str | None = None
    es_id: str | None = None
    download_count: int = 0

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=False)


class PaperSummary(BaseModel):
    id: str
    title: str
    authors: list[str]
    year: int | None = None
    venue: str | None = None
    abstract_snippet: str | None = None


class PaperRecommendation(BaseModel):
    paper: PaperSummary
    score: float


class PaperResponse(PaperInDB):
    recommendations: list[PaperRecommendation] = Field(default_factory=list)


class ViewHistoryEntry(BaseModel):
    user_id: str
    viewed_at: datetime = Field(default_factory=datetime.utcnow)
