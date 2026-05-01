"""Corpus storage module - JSON/Markdown file operations."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import (
    Source, Document, Node, Relationship, ScrapeJob,
    RelationshipType
)


class CorpusStorage:
    """File-based storage for the MoM Wiki corpus."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.corpus_dir = self.base_dir / "corpus"
        self.sources_file = self.base_dir / "sources.json"

    # === Source Operations ===

    def load_sources(self) -> list[Source]:
        """Load all configured sources."""
        if not self.sources_file.exists():
            return []
        with open(self.sources_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Source.model_validate(s) for s in data]

    def save_sources(self, sources: list[Source]) -> None:
        """Save all sources to file."""
        data = [s.model_dump(mode="json") for s in sources]
        with open(self.sources_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def get_source(self, source_id: str) -> Optional[Source]:
        """Get a source by ID."""
        sources = self.load_sources()
        for source in sources:
            if source.id == source_id:
                return source
        return None

    def add_source(self, source: Source) -> None:
        """Add a new source."""
        sources = self.load_sources()
        sources.append(source)
        self.save_sources(sources)

    def update_source(self, source: Source) -> None:
        """Update an existing source."""
        sources = self.load_sources()
        for i, s in enumerate(sources):
            if s.id == source.id:
                sources[i] = source
                break
        self.save_sources(sources)

    # === Document Operations ===

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        doc_file = self.corpus_dir / "documents" / f"{doc_id}.json"
        if not doc_file.exists():
            return None
        with open(doc_file, "r", encoding="utf-8") as f:
            return Document.model_validate(json.load(f))

    def get_document_by_checksum(self, source_id: str, checksum: str) -> Optional[Document]:
        """Find a document by source and checksum for dedup."""
        docs_dir = self.corpus_dir / "documents"
        if not docs_dir.exists():
            return None
        for doc_file in docs_dir.glob("*.json"):
            with open(doc_file, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
            if doc_data.get("source_id") == source_id and doc_data.get("checksum") == checksum:
                return Document.model_validate(doc_data)
        return None

    def save_document(self, document: Document, content: str) -> bool:
        """
        Save a document with checksum dedup.
        Returns True if created/updated, False if unchanged.
        """
        # Check for existing document with same checksum
        existing = self.get_document_by_checksum(document.source_id, document.checksum)
        if existing:
            return False  # Unchanged

        # Save document metadata
        docs_dir = self.corpus_dir / "documents"
        docs_dir.mkdir(parents=True, exist_ok=True)
        doc_file = docs_dir / f"{document.id}.json"

        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(document.model_dump(mode="json"), f, indent=2, default=str)

        # Save content
        content_dir = self.corpus_dir / "content"
        content_dir.mkdir(parents=True, exist_ok=True)
        content_file = content_dir / f"{document.id}.md"
        document.content_path = f"content/{document.id}.md"

        with open(content_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Update document with content path
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(document.model_dump(mode="json"), f, indent=2, default=str)

        return True

    def list_documents(self, source_id: Optional[str] = None) -> list[Document]:
        """List all documents, optionally filtered by source."""
        docs_dir = self.corpus_dir / "documents"
        if not docs_dir.exists():
            return []
        documents = []
        for doc_file in docs_dir.glob("*.json"):
            with open(doc_file, "r", encoding="utf-8") as f:
                doc = Document.model_validate(json.load(f))
            if source_id is None or doc.source_id == source_id:
                documents.append(doc)
        return documents

    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get the markdown content of a document."""
        content_file = self.corpus_dir / "content" / f"{doc_id}.md"
        if not content_file.exists():
            return None
        with open(content_file, "r", encoding="utf-8") as f:
            return f.read()

    # === Node Operations ===

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        node_file = self.corpus_dir / "nodes" / f"{node_id}.json"
        if not node_file.exists():
            return None
        with open(node_file, "r", encoding="utf-8") as f:
            return Node.model_validate(json.load(f))

    def get_node_by_name(self, name: str, node_type: str) -> Optional[Node]:
        """Find a node by name and type."""
        nodes_dir = self.corpus_dir / "nodes"
        if not nodes_dir.exists():
            return None
        for node_file in nodes_dir.glob("*.json"):
            with open(node_file, "r", encoding="utf-8") as f:
                node_data = json.load(f)
            if node_data.get("name") == name and node_data.get("type") == node_type:
                return Node.model_validate(node_data)
        return None

    def create_node(self, node: Node) -> Node:
        """Create a new node."""
        nodes_dir = self.corpus_dir / "nodes"
        nodes_dir.mkdir(parents=True, exist_ok=True)
        node_file = nodes_dir / f"{node.id}.json"

        with open(node_file, "w", encoding="utf-8") as f:
            json.dump(node.model_dump(mode="json"), f, indent=2, default=str)

        return node

    def update_node(self, node: Node) -> Node:
        """Update an existing node."""
        node.updated_at = datetime.utcnow()
        nodes_dir = self.corpus_dir / "nodes"
        node_file = nodes_dir / f"{node.id}.json"

        with open(node_file, "w", encoding="utf-8") as f:
            json.dump(node.model_dump(mode="json"), f, indent=2, default=str)

        return node

    def list_nodes(self, node_type: Optional[str] = None, realm: Optional[str] = None) -> list[Node]:
        """List all nodes, optionally filtered."""
        nodes_dir = self.corpus_dir / "nodes"
        if not nodes_dir.exists():
            return []
        nodes = []
        for node_file in nodes_dir.glob("*.json"):
            with open(node_file, "r", encoding="utf-8") as f:
                node = Node.model_validate(json.load(f))
            if node_type and node.type.value != node_type:
                continue
            if realm and (not node.attributes.realm or node.attributes.realm.value != realm):
                continue
            nodes.append(node)
        return nodes

    # === Relationship Operations ===

    def load_relationships(self) -> list[Relationship]:
        """Load all relationships."""
        rel_file = self.corpus_dir / "relationships.json"
        if not rel_file.exists():
            return []
        with open(rel_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Relationship.model_validate(r) for r in data]

    def save_relationships(self, relationships: list[Relationship]) -> None:
        """Save all relationships."""
        rel_file = self.corpus_dir / "relationships.json"
        rel_file.parent.mkdir(parents=True, exist_ok=True)
        data = [r.model_dump(mode="json") for r in relationships]
        with open(rel_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_relationship(self, relationship: Relationship) -> bool:
        """Add a relationship if it doesn't exist. Returns True if added."""
        relationships = self.load_relationships()
        # Check for duplicate
        for r in relationships:
            if r == relationship:
                return False
        relationships.append(relationship)
        self.save_relationships(relationships)
        return True

    def get_related_nodes(self, node_id: str, rel_type: Optional[RelationshipType] = None) -> list[dict]:
        """Get nodes related to a given node."""
        relationships = self.load_relationships()
        related = []
        for r in relationships:
            if rel_type and r.type != rel_type:
                continue
            if r.source_node_id == node_id:
                target = self.get_node(r.target_node_id)
                if target:
                    related.append({
                        "relationship": r,
                        "node": target,
                        "direction": "outgoing"
                    })
            elif r.target_node_id == node_id:
                source = self.get_node(r.source_node_id)
                if source:
                    related.append({
                        "relationship": r,
                        "node": source,
                        "direction": "incoming"
                    })
        return related

    # === ScrapeJob Operations ===

    def create_job(self, job: ScrapeJob) -> ScrapeJob:
        """Create a new scrape job record."""
        jobs_dir = self.corpus_dir / "jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        job_file = jobs_dir / f"{job.id}.json"

        with open(job_file, "w", encoding="utf-8") as f:
            json.dump(job.model_dump(mode="json"), f, indent=2, default=str)

        return job

    def update_job(self, job: ScrapeJob) -> ScrapeJob:
        """Update a scrape job record."""
        jobs_dir = self.corpus_dir / "jobs"
        job_file = jobs_dir / f"{job.id}.json"

        with open(job_file, "w", encoding="utf-8") as f:
            json.dump(job.model_dump(mode="json"), f, indent=2, default=str)

        return job

    def get_job(self, job_id: str) -> Optional[ScrapeJob]:
        """Get a scrape job by ID."""
        job_file = self.corpus_dir / "jobs" / f"{job_id}.json"
        if not job_file.exists():
            return None
        with open(job_file, "r", encoding="utf-8") as f:
            return ScrapeJob.model_validate(json.load(f))

    # === Utility Functions ===

    @staticmethod
    def compute_checksum(content: str | bytes) -> str:
        """Compute SHA256 checksum for content."""
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def update_stats(self) -> dict:
        """Update and return corpus statistics."""
        stats = {
            "document_count": len(self.list_documents()),
            "node_count": len(self.list_nodes()),
            "relationship_count": len(self.load_relationships()),
            "source_count": len(self.load_sources()),
            "last_updated": datetime.utcnow().isoformat(),
            "by_type": {},
            "by_realm": {}
        }

        # Count by type
        for node in self.list_nodes():
            type_key = node.type.value
            stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
            if node.attributes.realm:
                realm_key = node.attributes.realm.value
                stats["by_realm"][realm_key] = stats["by_realm"].get(realm_key, 0) + 1

        # Save stats
        stats_file = self.corpus_dir / "stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

        return stats
