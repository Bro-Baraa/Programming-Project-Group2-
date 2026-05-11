"""Composed competency router preserving the existing /competencies API surface."""

from fastapi import APIRouter

from .competencies_items import router as items_router
from .competencies_profiles import router as profiles_router
from .competencies_weights import router as weights_router

router = APIRouter(tags=["competencies"])

# Include routers with their prefixes
router.include_router(profiles_router, prefix="/competencies")
router.include_router(weights_router, prefix="/competencies")
router.include_router(items_router, prefix="/competencies")
