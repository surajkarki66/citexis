from pydantic import BaseModel

from app.core.constants import RecommendationReason
from app.core.schemas.paper import PaperSummary


class RecommendationItem(BaseModel):
    paper: PaperSummary
    reason: RecommendationReason
    score: float


class RecommendationResponse(BaseModel):
    paper_id: str
    items: list[RecommendationItem]
