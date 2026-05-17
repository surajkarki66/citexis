from fastapi import APIRouter, Query

from app.api.deps import KnowledgeGraphDep

router = APIRouter()


@router.get("/topics")
async def explore_topics(
    tag: str = Query(..., description="Topic tag, e.g. rl, nlp, llm"),
    kg: KnowledgeGraphDep,
) -> list[dict]:
    clusters = await kg.get_topic_clusters(tag)
    return [
        {
            "venue": c["_id"],
            "count": c["count"],
            "sample_titles": [p.get("title") for p in c.get("papers", [])[:3]],
        }
        for c in clusters
    ]
