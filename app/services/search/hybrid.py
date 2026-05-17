from app.config import Settings
from app.core.schemas.search import SearchFilters, SearchRequest, SearchResponse, SearchResult
from app.repositories.paper_repository import PaperRepository
from app.services.search.keyword import KeywordSearchService
from app.services.search.reranker import PassthroughReranker, Reranker
from app.services.search.rrf import reciprocal_rank_fusion
from app.services.search.semantic import SemanticSearchService


class HybridSearchService:
    def __init__(
        self,
        settings: Settings,
        paper_repo: PaperRepository,
        keyword: KeywordSearchService,
        semantic: SemanticSearchService,
        reranker: Reranker | None = None,
    ) -> None:
        self._settings = settings
        self._papers = paper_repo
        self._keyword = keyword
        self._semantic = semantic
        self._reranker = reranker or PassthroughReranker()

    async def search(self, request: SearchRequest) -> SearchResponse:
        k = self._settings.search_top_k_per_source
        es_ids, vec_ids = await self._run_parallel(request.query, request.filters, k)
        merged = reciprocal_rank_fusion([es_ids, vec_ids], k=self._settings.search_rrf_k)
        top_merged = [pid for pid, _ in merged[: self._settings.search_rerank_top_n]]

        docs = await self._papers.get_many_by_ids(top_merged)
        doc_map = {str(d["_id"]): d for d in docs}
        texts = [
            f"{doc_map[pid]['title']}\n{doc_map[pid].get('abstract', '')}"
            for pid in top_merged
            if pid in doc_map
        ]
        valid_ids = [pid for pid in top_merged if pid in doc_map]
        if texts:
            self._reranker.rerank(request.query, texts, self._settings.search_final_top_n)
            # Reranker returns reordered texts; map back by position for skeleton.
            final_ids = valid_ids[: self._settings.search_final_top_n]
        else:
            final_ids = top_merged

        final_ids = final_ids[: request.top_k]
        score_map = dict(merged)
        results: list[SearchResult] = []
        for pid in final_ids:
            if pid not in doc_map:
                continue
            results.append(
                SearchResult(
                    paper=self._papers.to_summary(doc_map[pid]),
                    score=score_map.get(pid, 0.0),
                    source="hybrid",
                )
            )

        return SearchResponse(query=request.query, results=results, total=len(results))

    async def _run_parallel(
        self, query: str, filters: SearchFilters, top_k: int
    ) -> tuple[list[str], list[str]]:
        import asyncio

        es_task = self._keyword.search(query, filters, top_k)
        vec_task = self._semantic.search(query, filters, top_k)
        return await asyncio.gather(es_task, vec_task)
