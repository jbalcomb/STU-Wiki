"""API routes for Master of Magic Wiki Corpus."""

from fastapi import APIRouter

from . import search, documents, nodes, sources

router = APIRouter()

# Register all route modules
router.include_router(search.router)
router.include_router(documents.router)
router.include_router(nodes.router)
router.include_router(sources.router)

__all__ = ["router"]
