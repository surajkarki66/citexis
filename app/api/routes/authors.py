from fastapi import APIRouter

from app.api.deps import KnowledgeGraphDep
router = APIRouter()


@router.get("/{author_name}/papers")
async def author_papers(author_name: str, kg: KnowledgeGraphDep) -> list[dict]:
    docs = await kg.get_author_papers(author_name)
    return [
        {
            "id": str(d["_id"]),
            "title": d.get("title"),
            "year": d.get("year"),
            "venue": d.get("venue"),
        }
        for d in docs
    ]
