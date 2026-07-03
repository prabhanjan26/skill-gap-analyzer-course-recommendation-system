"""Employee routes: role listing + resume upload / analysis (DDD 5.9, 5.10)."""
from __future__ import annotations

import logging
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.mongodb import COMPETENCY_MATRIX, get_mongo_db
from app.models.schemas import AnalysisResponse, ApiResponse
from app.services import analysis_orchestrator, llm_service
from app.services.resume_parser import (
    CorruptedFileError,
    InsufficientContentError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/employee", tags=["employee"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream",  # some browsers send this for docx
}


def _ok(data=None, message=None, status_code=200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(success=True, data=data, message=message).model_dump(),
    )


def _err(message: str, status_code: int, errors: Optional[List[str]] = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(success=False, message=message, errors=errors).model_dump(),
    )


# ---------------------------------------------------------------------------
# 5.9 List available roles (for the selector)
# ---------------------------------------------------------------------------
@router.get("/roles")
async def list_roles() -> JSONResponse:
    db = get_mongo_db()
    cursor = db[COMPETENCY_MATRIX].find({}, {"role_name": 1, "role_slug": 1, "skills": 1})
    roles = []
    async for doc in cursor:
        roles.append(
            {
                "role_name": doc["role_name"],
                "role_slug": doc["role_slug"],
                "skills_count": len(doc.get("skills", [])),
            }
        )
    return _ok(data={"roles": roles})


# ---------------------------------------------------------------------------
# 5.10 Upload resume & trigger analysis
# ---------------------------------------------------------------------------
@router.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    role_slug: str = Form(...),
    employee_name: str = Form(default=""),
) -> JSONResponse:
    settings = get_settings()

    # --- File type validation (extension + content-type) ---
    ext = os.path.splitext(resume.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS and (resume.content_type or "") not in ALLOWED_CONTENT_TYPES:
        return _err("Invalid file type. Accepted: PDF, DOCX", 400)

    # --- Read content + size validation ---
    content = await resume.read()
    if len(content) == 0:
        return _err("Empty file uploaded", 400)
    if len(content) > settings.max_file_size_bytes:
        return _err("File exceeds 5MB limit", 413)

    # --- Role existence check ---
    db = get_mongo_db()
    role_doc = await db[COMPETENCY_MATRIX].find_one({"role_slug": role_slug})
    if not role_doc:
        return _err("Role not found", 404)

    # --- Persist to a temp file ---
    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_ext = ext if ext in ALLOWED_EXTENSIONS else ".pdf"
    tmp_path = os.path.join(settings.upload_dir, f"{uuid.uuid4().hex}{safe_ext}")
    with open(tmp_path, "wb") as fh:
        fh.write(content)

    try:
        result = await run_in_threadpool(
            analysis_orchestrator.run_analysis,
            tmp_path,
            resume.content_type or "",
            role_doc,
            employee_name,
        )
        # Validate/normalize against the response schema.
        validated = AnalysisResponse(**result)
        return _ok(data=validated.model_dump())

    except UnsupportedFileTypeError:
        return _err("Invalid file type. Accepted: PDF, DOCX", 400)
    except InsufficientContentError as exc:
        return _err(str(exc) or "Insufficient text content", 422)
    except CorruptedFileError as exc:
        return _err(str(exc) or "Could not read the uploaded file", 422)
    except llm_service.LLMRateLimitError as exc:
        logger.warning("LLM rate limit: %s", exc)
        return _err("LLM rate limit reached. Retry in 60 seconds.", 429)
    except llm_service.LLMTimeoutError as exc:
        logger.warning("LLM timeout: %s", exc)
        return _err("LLM service timeout", 504)
    except llm_service.LLMContentBlockedError as exc:
        logger.warning("LLM content blocked: %s", exc)
        return _err("Resume flagged by safety filter. Please review and re-upload.", 422)
    except llm_service.LLMConfigError as exc:
        logger.error("LLM configuration error: %s", exc)
        return _err("Configuration error - contact admin", 500, errors=[str(exc)])
    except Exception as exc:  # pragma: no cover - catch-all pipeline error
        logger.exception("Analysis pipeline error")
        return _err("Analysis pipeline error", 500, errors=[str(exc)])
    finally:
        # Resume files are deleted after pipeline completion (DDD 1.2).
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass
