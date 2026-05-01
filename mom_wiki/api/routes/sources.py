"""Source API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from ...models import Source, SourceType, SourceStatus
from ...storage import CorpusStorage
from ...scrapers import get_scraper

router = APIRouter(prefix="/sources", tags=["sources"])

_storage = CorpusStorage()


class SourceCreate(BaseModel):
    """Request body for creating a source."""
    name: str
    type: str  # "web", "pdf", "lbx"
    location: str


class SourceUpdate(BaseModel):
    """Request body for updating a source."""
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    enabled: Optional[bool] = None


@router.get("")
async def list_sources(
    type: Optional[str] = Query(None, description="Filter by source type"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """List all configured sources."""
    sources = _storage.load_sources()

    # Filter by type
    if type:
        sources = [s for s in sources if s.type.value == type]

    # Filter by status
    if status:
        sources = [s for s in sources if s.last_status.value == status]

    return {
        "count": len(sources),
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type.value,
                "location": s.location,
                "status": s.last_status.value,
                "enabled": s.enabled,
                "last_scraped": s.last_scraped.isoformat() if s.last_scraped else None,
                "error_message": s.last_error
            }
            for s in sources
        ]
    }


@router.post("")
async def create_source(source_data: SourceCreate):
    """Create a new source."""
    try:
        source_type = SourceType(source_data.type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source type: {source_data.type}. Valid types: web, pdf, lbx"
        )

    source = Source(
        name=source_data.name,
        type=source_type,
        location=source_data.location,
        enabled=True
    )

    _storage.add_source(source)

    return {
        "id": source.id,
        "name": source.name,
        "type": source.type.value,
        "location": source.location,
        "status": source.last_status.value,
        "enabled": source.enabled
    }


@router.get("/{source_id}")
async def get_source(source_id: str):
    """Get a specific source by ID."""
    source = _storage.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return {
        "id": source.id,
        "name": source.name,
        "type": source.type.value,
        "location": source.location,
        "status": source.last_status.value,
        "enabled": source.enabled,
        "last_scraped": source.last_scraped.isoformat() if source.last_scraped else None,
        "error_message": source.last_error,
        "created_at": source.created_at.isoformat() if source.created_at else None
    }


@router.put("/{source_id}")
async def update_source(source_id: str, update: SourceUpdate):
    """Update a source."""
    source = _storage.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if update.name:
        source.name = update.name
    if update.location:
        source.location = update.location
    if update.status:
        try:
            source.last_status = SourceStatus(update.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")
    if update.enabled is not None:
        source.enabled = update.enabled

    _storage.update_source(source)

    return {"status": "updated", "id": source_id}


@router.delete("/{source_id}")
async def delete_source(source_id: str):
    """Delete a source."""
    sources = _storage.load_sources()
    original_count = len(sources)
    sources = [s for s in sources if s.id != source_id]

    if len(sources) == original_count:
        raise HTTPException(status_code=404, detail="Source not found")

    _storage.save_sources(sources)

    return {"status": "deleted", "id": source_id}


def _run_scrape(source_id: str, job_id: str):
    """Background task: run scraper, recording progress against the given job."""
    source = _storage.get_source(source_id)
    job = _storage.get_job(job_id)
    if not source or not job:
        return

    try:
        scraper = get_scraper(source, _storage)
        scraper.process_source(source, job=job)
    except Exception as e:
        # Belt-and-suspenders: process_source already handles its own errors,
        # but if scraper construction itself blows up, mark the job + source.
        job.add_error(str(e))
        job.complete(success=False)
        _storage.update_job(job)
        source.mark_failed(str(e))
        _storage.update_source(source)


@router.post("/{source_id}/scrape")
async def trigger_scrape(source_id: str, background_tasks: BackgroundTasks):
    """
    Trigger a scrape for a specific source.

    The scrape runs in the background. Use GET /jobs/{id} to check status.
    """
    source = _storage.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    from ...models import ScrapeJob
    job = ScrapeJob(source_id=source_id)
    _storage.create_job(job)

    background_tasks.add_task(_run_scrape, source_id, job.id)

    return {
        "status": "started",
        "job_id": job.id,
        "source_id": source_id
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get the status of a scrape job."""
    job = _storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "source_id": job.source_id,
        "status": job.status.value,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "documents_created": job.documents_created,
        "documents_updated": job.documents_updated,
        "documents_unchanged": job.documents_unchanged,
        "nodes_created": len(job.nodes_created),
        "errors": [
            {"message": e.message, "url": e.url, "timestamp": e.timestamp.isoformat()}
            for e in job.errors
        ]
    }
