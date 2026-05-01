"""Data models for Master of Magic Wiki Corpus."""

from .source import Source, SourceType, SourceStatus
from .document import Document, DocumentMetadata
from .node import Node, NodeType, NodeAttributes, Realm, Rarity
from .relationship import Relationship, RelationshipType
from .scrape_job import ScrapeJob, JobStatus, JobError

__all__ = [
    # Source
    "Source",
    "SourceType",
    "SourceStatus",
    # Document
    "Document",
    "DocumentMetadata",
    # Node
    "Node",
    "NodeType",
    "NodeAttributes",
    "Realm",
    "Rarity",
    # Relationship
    "Relationship",
    "RelationshipType",
    # ScrapeJob
    "ScrapeJob",
    "JobStatus",
    "JobError",
]
