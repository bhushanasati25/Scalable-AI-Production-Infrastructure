"""
API v1 Router — Aggregates all v1 endpoint modules.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.tasks import router as tasks_router
from app.api.v1.inference import router as inference_router
from app.api.v1.users import router as users_router

router = APIRouter()
router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
router.include_router(inference_router, prefix="/inference", tags=["Inference"])
router.include_router(users_router, prefix="/users", tags=["Users"])
