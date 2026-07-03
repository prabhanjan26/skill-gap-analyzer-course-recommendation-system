"""Admin routes: role CRUD + category listing (DDD 5.3-5.8, 11.1, 11.2)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError
from slugify import slugify

from app.constants.categories import category_choices
from app.db.mongodb import COMPETENCY_MATRIX, get_mongo_db
from app.models.schemas import ApiResponse, RoleCreate, RoleUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize_role(doc: Dict) -> Dict:
    """Convert a Mongo role document into a JSON-safe dict."""
    doc = dict(doc)
    doc["_id"] = str(doc["_id"])
    return doc


def _ok(data=None, message=None, status_code=200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(success=True, data=data, message=message).model_dump(),
    )


def _err(message: str, status_code: int, errors: List[str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(success=False, message=message, errors=errors).model_dump(),
    )


# ---------------------------------------------------------------------------
# 5.3 List categories
# ---------------------------------------------------------------------------
@router.get("/categories")
async def list_categories() -> JSONResponse:
    return _ok(data={"categories": category_choices()})


# ---------------------------------------------------------------------------
# 5.4 List all roles
# ---------------------------------------------------------------------------
@router.get("/roles")
async def list_roles() -> JSONResponse:
    db = get_mongo_db()
    cursor = db[COMPETENCY_MATRIX].find({})
    roles: List[Dict] = []
    async for doc in cursor:
        skills = doc.get("skills", [])
        roles.append(
            {
                "_id": str(doc["_id"]),
                "role_name": doc["role_name"],
                "role_slug": doc["role_slug"],
                "skills_count": len(skills),
                "categories": sorted({s["category"] for s in skills}),
                "updated_at": doc.get("updated_at"),
            }
        )
    return _ok(data={"roles": roles})


# ---------------------------------------------------------------------------
# 5.5 Get role detail
# ---------------------------------------------------------------------------
@router.get("/roles/{role_slug}")
async def get_role(role_slug: str) -> JSONResponse:
    db = get_mongo_db()
    doc = await db[COMPETENCY_MATRIX].find_one({"role_slug": role_slug})
    if not doc:
        return _err("Role not found", 404)
    return _ok(data={"role": _serialize_role(doc)})


# ---------------------------------------------------------------------------
# 5.6 Create role
# ---------------------------------------------------------------------------
@router.post("/roles")
async def create_role(payload: RoleCreate) -> JSONResponse:
    db = get_mongo_db()
    collection = db[COMPETENCY_MATRIX]

    role_slug = slugify(payload.role_name)

    # Uniqueness checks (name + slug).
    existing = await collection.find_one(
        {"$or": [{"role_name": payload.role_name}, {"role_slug": role_slug}]}
    )
    if existing:
        return _err("Duplicate role name", 409)

    now = _now_iso()
    document = {
        "role_name": payload.role_name,
        "role_slug": role_slug,
        "description": payload.description or "",
        "skills": [s.model_dump() for s in payload.skills],
        "created_at": now,
        "updated_at": now,
    }

    try:
        result = await collection.insert_one(document)
    except DuplicateKeyError:
        return _err("Duplicate role name", 409)

    document["_id"] = str(result.inserted_id)
    return _ok(data={"role": document}, message="Role created", status_code=201)


# ---------------------------------------------------------------------------
# 5.7 Update role (edit)
# ---------------------------------------------------------------------------
@router.put("/roles/{role_slug}")
async def update_role(role_slug: str, payload: RoleUpdate) -> JSONResponse:
    db = get_mongo_db()
    collection = db[COMPETENCY_MATRIX]

    doc = await collection.find_one({"role_slug": role_slug})
    if not doc:
        return _err("Role not found", 404)

    updates: Dict = {}

    if payload.role_name is not None and payload.role_name != doc["role_name"]:
        new_slug = slugify(payload.role_name)
        # Ensure the new name/slug does not collide with a different role.
        clash = await collection.find_one(
            {
                "$and": [
                    {"_id": {"$ne": doc["_id"]}},
                    {"$or": [{"role_name": payload.role_name}, {"role_slug": new_slug}]},
                ]
            }
        )
        if clash:
            return _err("Duplicate role name", 409)
        updates["role_name"] = payload.role_name
        updates["role_slug"] = new_slug

    if payload.description is not None:
        updates["description"] = payload.description

    if payload.skills is not None:
        updates["skills"] = [s.model_dump() for s in payload.skills]

    updates["updated_at"] = _now_iso()

    try:
        await collection.update_one({"_id": doc["_id"]}, {"$set": updates})
    except DuplicateKeyError:
        return _err("Duplicate role name", 409)

    updated = await collection.find_one({"_id": doc["_id"]})
    return _ok(data={"role": _serialize_role(updated)}, message="Role updated")


# ---------------------------------------------------------------------------
# 5.8 Delete role
# ---------------------------------------------------------------------------
@router.delete("/roles/{role_slug}")
async def delete_role(role_slug: str) -> JSONResponse:
    db = get_mongo_db()
    result = await db[COMPETENCY_MATRIX].delete_one({"role_slug": role_slug})
    if result.deleted_count == 0:
        return _err("Role not found", 404)
    return _ok(message="Role deleted")
