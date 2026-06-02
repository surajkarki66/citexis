import asyncio

from celery import Celery
from celery.signals import worker_process_init

from app.config import get_settings
from app.db.indexes import ensure_paper_indexes
from app.db.mongodb import get_database

settings = get_settings()


@worker_process_init.connect
def _ensure_mongodb_indexes(**_kwargs) -> None:
    asyncio.run(ensure_paper_indexes(get_database(settings)))

celery_app = Celery(
    "citexis",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
