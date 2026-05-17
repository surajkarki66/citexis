from app.config import Settings
from app.core.constants import RecommendationReason
from app.core.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.repositories.paper_repository import PaperRepository
from app.repositories.user_repository import UserInteractionRepository
from app.services.recommendations.citation_graph import CitationGraphRecommender
from app.services.recommendations.collaborative import CollaborativeRecommender
from app.services.recommendations.content_based import ContentBasedRecommender
from motor.motor_asyncio import AsyncIOMotorDatabase


class RecommendationEngine:
    WEIGHTS = {
        RecommendationReason.SEMANTIC: 0.5,
        RecommendationReason.CITATION: 0.3,
        RecommendationReason.COLLABORATIVE: 0.2,
    }

    def __init__(
        self,
        settings: Settings,
        db: AsyncIOMotorDatabase,
        paper_repo: PaperRepository,
        user_repo: UserInteractionRepository,
    ) -> None:
        self._papers = paper_repo
        self._content = ContentBasedRecommender(settings, paper_repo)
        self._citation = CitationGraphRecommender(db)
        self._collab = CollaborativeRecommender(user_repo)

    async def get_related(self, paper_id: str, limit: int = 10) -> RecommendationResponse:
        import asyncio

        semantic_ids, citation_ids, collab_ids = await asyncio.gather(
            self._content.recommend(paper_id),
            self._citation.recommend(paper_id),
            self._collab.recommend(paper_id),
        )

        scored: dict[str, tuple[float, RecommendationReason]] = {}
        for reason, ids in [
            (RecommendationReason.SEMANTIC, semantic_ids),
            (RecommendationReason.CITATION, citation_ids),
            (RecommendationReason.COLLABORATIVE, collab_ids),
        ]:
            weight = self.WEIGHTS[reason]
            for rank, pid in enumerate(ids, start=1):
                if pid == paper_id:
                    continue
                prev = scored.get(pid)
                score = weight / rank
                if prev is None or score > prev[0]:
                    scored[pid] = (score, reason)

        ranked = sorted(scored.items(), key=lambda x: x[1][0], reverse=True)[:limit]
        paper_ids = [pid for pid, _ in ranked]
        docs = await self._papers.get_many_by_ids(paper_ids)
        doc_map = {str(d["_id"]): d for d in docs}

        items: list[RecommendationItem] = []
        for pid, (score, reason) in ranked:
            if pid not in doc_map:
                continue
            items.append(
                RecommendationItem(
                    paper=self._papers.to_summary(doc_map[pid]),
                    reason=reason,
                    score=score,
                )
            )

        return RecommendationResponse(paper_id=paper_id, items=items)
