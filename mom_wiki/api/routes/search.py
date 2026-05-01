"""Search API routes."""

from typing import Optional
from fastapi import APIRouter, Query

from ...storage import CorpusStorage
from ...search import SearchIndex

router = APIRouter(prefix="/search", tags=["search"])

# Shared storage instance
_storage = CorpusStorage()
_search_index = SearchIndex(_storage)


@router.get("")
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    type: Optional[str] = Query(None, description="Filter: 'document' or 'node'"),
    node_type: Optional[str] = Query(None, description="Filter by node type (spell, unit, etc.)"),
    realm: Optional[str] = Query(None, description="Filter by magic realm")
):
    """
    Search the corpus.

    Returns documents and nodes matching the query, with highlights.
    """
    results = _search_index.search(
        query=q,
        limit=limit,
        item_type=type,
        node_type=node_type,
        realm=realm
    )

    return {
        "query": q,
        "count": len(results),
        "results": [
            {
                "id": r.id,
                "type": r.type,
                "title": r.title,
                "summary": r.summary,
                "score": r.score,
                "highlights": r.highlights,
                "metadata": r.metadata
            }
            for r in results
        ]
    }


@router.post("/rebuild")
async def rebuild_index():
    """Rebuild the search index."""
    count = _search_index.build()
    return {
        "status": "ok",
        "indexed_count": count
    }
