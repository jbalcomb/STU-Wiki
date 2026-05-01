"""Document model - a piece of scraped content."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class DocumentMetadata(BaseModel):
    """Metadata associated with a document."""
    author: Optional[str] = None
    publish_date: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """A piece of scraped content with metadata."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    title: str
    content_path: str  # Relative path to .md file in corpus/content/
    content_type: str = "text/markdown"
    url: Optional[str] = None  # Original URL for web sources
    file_path: Optional[str] = None  # Original file path for local sources
    drive_url: Optional[str] = None  # Google Drive link for binary source
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: str  # SHA256 of source content for dedup
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    node_ids: list[str] = Field(default_factory=list)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }

    def add_node(self, node_id: str) -> None:
        """Associate a node with this document."""
        if node_id not in self.node_ids:
            self.node_ids.append(node_id)
