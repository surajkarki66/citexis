def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """
    Merge ranked paper IDs via RRF: score(d) = sum 1 / (k + rank(d)).
    Returns (paper_id, score) sorted descending.
    """
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, paper_id in enumerate(ranked, start=1):
            scores[paper_id] = scores.get(paper_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
