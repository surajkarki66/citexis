from pydantic import BaseModel

from app.core.schemas.paper import PaperSummary


class RecommendationItem(BaseModel):
    paper: PaperSummary
    score: float


class RecommendationResponse(BaseModel):
    paper_id: str
    items: list[RecommendationItem]
