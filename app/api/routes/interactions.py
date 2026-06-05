from fastapi import APIRouter, HTTPException, status

from app.api.deps import PaperRepoDep, UserRepoDep
from app.core.schemas.user import UserInteractionCreate

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def record_interaction(
    body: UserInteractionCreate,
    papers: PaperRepoDep,
    users: UserRepoDep,
) -> dict:
    if not await papers.get_by_id(body.paper_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    interaction_id = await users.record(body)
    return {"id": interaction_id, "status": "recorded"}


@router.get("/users/{user_id}/saved")
async def list_saved_papers(user_id: str, users: UserRepoDep) -> dict:
    paper_ids = await users.get_saved_paper_ids(user_id)
    return {"user_id": user_id, "paper_ids": paper_ids}


@router.delete("/users/{user_id}/saved/{paper_id}")
async def unsave_paper(user_id: str, paper_id: str, users: UserRepoDep) -> dict:
    removed = await users.remove_save(user_id, paper_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Save not found")
    return {"status": "removed", "paper_id": paper_id}
