from app.repositories.user_repository import UserInteractionRepository


class CollaborativeRecommender:
    def __init__(self, user_repo: UserInteractionRepository) -> None:
        self._users = user_repo

    async def recommend(self, paper_id: str, limit: int = 20) -> list[str]:
        return await self._users.get_co_occurring_papers(paper_id, limit=limit)
