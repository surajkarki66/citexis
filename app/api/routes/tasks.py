from app.api.auth_deps import AdminUserDep
from celery.result import AsyncResult
from fastapi import APIRouter

from app.workers.celery_app import celery_app

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(task_id: str, _: AdminUserDep) -> dict:
    """Poll Celery task state and result (used by bulk JSON import UI)."""
    result = AsyncResult(task_id, app=celery_app)
    payload: dict = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
    }

    if result.successful():
        payload["result"] = result.result
        return payload

    if result.failed():
        payload["error"] = str(result.result)
        return payload

    return payload
