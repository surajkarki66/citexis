from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.deps import wire_app_state
from app.api.routes import api_router
from app.config import get_settings
from app.db.elasticsearch import close_elasticsearch
from app.db.indexes import ensure_paper_indexes
from app.db.mongodb import close_mongodb, get_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = get_database(settings)
    await ensure_paper_indexes(db)
    wire_app_state(app)
    await app.state.auth_service.ensure_bootstrap_admin()
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
