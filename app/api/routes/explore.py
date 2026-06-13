from fastapi import APIRouter, Query

from app.api.deps import ExploreDep

router = APIRouter()


@router.get("/topics")
async def explore_topics(
    explore: ExploreDep,
    tag: str = Query(..., description="Topic search — matches similar tags in the corpus"),
) -> list[dict]:
    clusters = await explore.get_tag_clusters(tag)
    return [
        {
            "tag": c["_id"],
            "count": c["count"],
            "papers": [
                {"id": str(p["_id"]), "title": p.get("title")}
                for p in c.get("papers", [])
            ],
        }
        for c in clusters
    ]


@router.get("/papers/{paper_id}/neighbors")
async def citation_neighbors(
    paper_id: str,
    explore: ExploreDep,
) -> list[str]:
    return await explore.get_citation_neighbors(paper_id)
