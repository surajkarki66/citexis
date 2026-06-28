from fastapi import APIRouter, HTTPException, status

from app.api.auth_deps import CurrentUserDep, CurrentUserOptionalDep
from app.api.deps import PaperRepoDep, UserRepoDep
from app.core.constants import InteractionType
from app.core.schemas.user import InteractionCreate, UserInteractionCreate

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def record_interaction(
    body: InteractionCreate,
    user: CurrentUserDep,
    papers: PaperRepoDep,
    users: UserRepoDep,
) -> dict:
    if body.interaction_type == InteractionType.RATING and body.rating is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rating is required when interaction_type is rating",
        )
    if not await papers.get_by_id(body.paper_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    interaction = UserInteractionCreate(user_id=user.id, **body.model_dump())
    interaction_id = await users.record(interaction)
    return {"id": interaction_id, "status": "recorded"}


@router.get("/me/papers/{paper_id}/rating")
async def get_my_paper_rating(
    paper_id: str,
    user: CurrentUserDep,
    users: UserRepoDep,
) -> dict:
    rating = await users.get_rating(user.id, paper_id)
    return {"user_id": user.id, "paper_id": paper_id, "rating": rating}


@router.get("/me/saved")
async def list_my_saved_papers(user: CurrentUserDep, users: UserRepoDep) -> dict:
    paper_ids = await users.get_saved_paper_ids(user.id)
    return {"user_id": user.id, "paper_ids": paper_ids}


@router.delete("/me/saved/{paper_id}")
async def unsave_my_paper(
    paper_id: str,
    user: CurrentUserDep,
    users: UserRepoDep,
) -> dict:
    removed = await users.remove_save(user.id, paper_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Save not found")
    return {"status": "removed", "paper_id": paper_id}


@router.post("/views/{paper_id}", status_code=status.HTTP_201_CREATED)
async def record_view(
    paper_id: str,
    user: CurrentUserOptionalDep,
    papers: PaperRepoDep,
    users: UserRepoDep,
) -> dict:
    """Record a paper view when the user is signed in."""
    if user is None:
        return {"status": "skipped"}
    if not await papers.get_by_id(paper_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    interaction = UserInteractionCreate(
        user_id=user.id,
        paper_id=paper_id,
        interaction_type=InteractionType.VIEW,
    )
    interaction_id = await users.record(interaction)
    return {"id": interaction_id, "status": "recorded"}


@router.post("/clicks/{paper_id}", status_code=status.HTTP_201_CREATED)
async def record_click(
    paper_id: str,
    user: CurrentUserOptionalDep,
    papers: PaperRepoDep,
    users: UserRepoDep,
) -> dict:
    """Record a paper click when the user is signed in."""
    if user is None:
        return {"status": "skipped"}
    if not await papers.get_by_id(paper_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    interaction = UserInteractionCreate(
        user_id=user.id,
        paper_id=paper_id,
        interaction_type=InteractionType.CLICK,
    )
    interaction_id = await users.record(interaction)
    return {"id": interaction_id, "status": "recorded"}
