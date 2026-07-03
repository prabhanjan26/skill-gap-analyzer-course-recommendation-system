"""FastAPI application entrypoint: CORS, lifespan, routers, error envelope."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.chromadb_client import get_chroma_client, get_course_collection
from app.db.mongodb import close_mongo, connect_mongo
from app.models.schemas import ApiResponse
from app.routes import admin, employee, health
from app.services.course_embedding_pipeline import auto_embed_on_startup

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.main")

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB clients and self-heal the course index at startup."""
    logger.info("Starting Skill Gap Analyzer backend...")

    # ChromaDB (persistent client + collections).
    get_chroma_client()
    get_course_collection()

    # MongoDB (with retry).
    try:
        await connect_mongo()
    except RuntimeError as exc:
        logger.error("MongoDB unavailable at startup: %s", exc)

    # Course embedding self-heal / incremental embed (DDD 10.3).
    try:
        await auto_embed_on_startup()
    except Exception as exc:  # pragma: no cover
        logger.error("Course embedding pipeline error at startup: %s", exc)

    logger.info("Startup complete.")
    yield

    await close_mongo()
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Skill Gap Analyzer & Course Recommender",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return validation errors in the standard response envelope (DDD 5.6)."""
    errors = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", []) if p != "body")
        msg = err.get("msg", "invalid value")
        errors.append(f"{loc}: {msg}" if loc else msg)
    return JSONResponse(
        status_code=422,
        content=ApiResponse(
            success=False, message="Validation error", errors=errors
        ).model_dump(),
    )


app.include_router(health.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(employee.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return ApiResponse(
        success=True,
        data={"service": "Skill Gap Analyzer API", "docs": "/docs", "api": API_PREFIX},
        message="OK",
    ).model_dump()
