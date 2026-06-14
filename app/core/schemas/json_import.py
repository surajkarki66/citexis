from pydantic import BaseModel, Field, field_validator

from app.core.schemas.paper import AuthorSchema, PaperCreate

REQUIRED_JSON_FIELDS = (
    "title",
    "authors",
    "abstract",
    "year",
    "venue",
    "tags",
    "full_text_url",
)


class JsonBulkPaperImport(BaseModel):
    """Strict payload for bulk JSON import — complete metadata, no CORE enrichment."""

    title: str = Field(min_length=1)
    authors: list[AuthorSchema] = Field(min_length=1)
    abstract: str = Field(min_length=1)
    year: int
    venue: str = Field(min_length=1)
    tags: list[str] = Field(min_length=1)
    full_text_url: str = Field(min_length=1)
    doi: str | None = None
    citations: list[str] = Field(default_factory=list)
    cited_by_count: int = 0

    @field_validator("tags")
    @classmethod
    def tags_non_empty(cls, value: list[str]) -> list[str]:
        cleaned = [tag.strip() for tag in value if tag.strip()]
        if not cleaned:
            raise ValueError("tags must contain at least one non-empty tag")
        return cleaned

    def to_paper_create(self) -> PaperCreate:
        return PaperCreate(
            title=self.title.strip(),
            authors=self.authors,
            abstract=self.abstract.strip(),
            year=self.year,
            venue=self.venue.strip(),
            tags=self.tags,
            full_text_url=self.full_text_url.strip(),
            doi=self.doi,
            citations=self.citations,
            cited_by_count=self.cited_by_count,
        )
