from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.deps import wire_app_state
from app.api.routes import api_router
from app.config import get_settings
from app.db.elasticsearch import close_elasticsearch
from app.db.mongodb import close_mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    wire_app_state(app)
    yield
    await close_mongodb()
    await close_elasticsearch()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Citexis",
        description="Hybrid academic paper discovery API",
        version=__version__,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
