import asyncio

from app.config import Settings
from app.core.constants import RecommendationReason
from app.core.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.repositories.paper_repository import PaperRepository
from app.repositories.user_repository import UserInteractionRepository
from app.services.recommendations.citation import CitationBasedRecommender
from app.services.recommendations.collaborative import CollaborativeRecommender
from app.services.recommendations.content_based import ContentBasedRecommender
from motor.motor_asyncio import AsyncIOMotorDatabase
from collections import defaultdict


class RecommendationEngine:
    WEIGHTS = {
        RecommendationReason.SEMANTIC: 0.5,
        RecommendationReason.CITATION: 0.3,
        RecommendationReason.COLLABORATIVE: 0.2,
    }

    K = 60  # RRF constant

    def __init__(
        self,
        settings: Settings,
        db: AsyncIOMotorDatabase,
        paper_repo: PaperRepository,
        user_repo: UserInteractionRepository,
    ) -> None:
        self._papers = paper_repo
        self._content = ContentBasedRecommender(settings, paper_repo)
        self._citation = CitationBasedRecommender(db)
        self._collab = CollaborativeRecommender(user_repo)

    async def get_related(self, paper_id: str, limit: int = 10) -> RecommendationResponse:

        semantic_ids, citation_ids, collab_ids = await asyncio.gather(
            self._content.recommend(paper_id),
            self._citation.recommend(paper_id),
            self._collab.recommend(paper_id),
        )

        # remove duplicates within each list
        semantic_ids = list(dict.fromkeys(semantic_ids))
        citation_ids = list(dict.fromkeys(citation_ids))
        collab_ids = list(dict.fromkeys(collab_ids))

        # fused scoring (no reasons anymore)
        scored = defaultdict(float)

        for reason, ids in [
            (RecommendationReason.SEMANTIC, semantic_ids),
            (RecommendationReason.CITATION, citation_ids),
            (RecommendationReason.COLLABORATIVE, collab_ids),
        ]:
            weight = self.WEIGHTS[reason]

            for rank, pid in enumerate(ids, start=1):
                if pid == paper_id:
                    continue

                score = weight / (self.K + rank)
                scored[pid] += score

        ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)[:limit]
        paper_ids = [pid for pid, _ in ranked]

        docs = await self._papers.get_many_by_ids(paper_ids)
        doc_map = {str(d["_id"]): d for d in docs}

        items: list[RecommendationItem] = []

        for pid, score in ranked:
            if pid not in doc_map:
                continue

            items.append(
                RecommendationItem(
                    paper=self._papers.to_summary(doc_map[pid]),
                    score=score,
                )
            )

        return RecommendationResponse(paper_id=paper_id, items=items)