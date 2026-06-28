from datetime import datetime

from pydantic import BaseModel, Field

from app.core.constants import InteractionType


class InteractionCreate(BaseModel):
    paper_id: str
    interaction_type: InteractionType
    rating: float | None = Field(default=None, ge=0, le=5)


class UserInteractionCreate(InteractionCreate):
    user_id: str


class UserInteractionInDB(UserInteractionCreate):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}
