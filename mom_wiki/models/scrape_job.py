"""ScrapeJob model - record of scraping execution."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class JobStatus(str, Enum):
    """Status of a scrape job."""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobError(BaseModel):
    """An error that occurred during scraping."""
    message: str
    url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }


class ScrapeJob(BaseModel):
    """Record of a scraping execution."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.RUNNING
    documents_created: int = 0
    documents_updated: int = 0
    documents_unchanged: int = 0
    nodes_created: list[str] = Field(default_factory=list)
    errors: list[JobError] = Field(default_factory=list)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }

    def add_error(self, message: str, url: Optional[str] = None) -> None:
        """Record an error during scraping."""
        self.errors.append(JobError(message=message, url=url))

    def complete(self, success: bool = True) -> None:
        """Mark the job as complete."""
        self.completed_at = datetime.utcnow()
        self.status = JobStatus.SUCCESS if success else JobStatus.FAILED

    def cancel(self) -> None:
        """Mark the job as cancelled."""
        self.completed_at = datetime.utcnow()
        self.status = JobStatus.CANCELLED

    @property
    def total_documents(self) -> int:
        """Total documents processed."""
        return self.documents_created + self.documents_updated + self.documents_unchanged
