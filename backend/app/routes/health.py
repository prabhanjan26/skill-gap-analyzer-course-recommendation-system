"""Health check endpoint (DDD 5.2)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.chromadb_client import chroma_health, courses_indexed_count
from app.db.mongodb import mongo_health
from app.models.schemas import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    mongo_status = await mongo_health()
    chroma_status = chroma_health()
    courses = courses_indexed_count()

    data = {
        "api": "ok",
        "mongodb": mongo_status,
        "chromadb": chroma_status,
        "courses_indexed": courses,
    }
    all_ok = mongo_status == "ok" and chroma_status == "ok"
    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(
            success=all_ok,
            data=data,
            message="All systems operational" if all_ok else "One or more components unhealthy",
        ).model_dump(),
    )
