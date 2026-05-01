"""Source model - configured data origin for scraping."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class SourceType(str, Enum):
    """Type of data source."""
    WEB = "web"
    PDF = "pdf"
    LBX = "lbx"


class SourceStatus(str, Enum):
    """Status of last scrape attempt."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Source(BaseModel):
    """A configured data origin for scraping."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: SourceType
    name: str
    location: str  # URL for web, file path for pdf/lbx
    drive_id: Optional[str] = None  # Google Drive file ID for binaries
    schedule: Optional[str] = None  # Cron expression for auto-scrape
    enabled: bool = True
    last_scraped: Optional[datetime] = None
    last_status: SourceStatus = SourceStatus.PENDING
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }

    def mark_success(self) -> None:
        """Mark the source as successfully scraped."""
        self.last_scraped = datetime.utcnow()
        self.last_status = SourceStatus.SUCCESS
        self.last_error = None
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark the source as failed with an error message."""
        self.last_scraped = datetime.utcnow()
        self.last_status = SourceStatus.FAILED
        self.last_error = error
        self.updated_at = datetime.utcnow()
