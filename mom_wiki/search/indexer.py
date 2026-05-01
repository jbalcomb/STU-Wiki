"""Search index builder and query engine."""

import json
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import logging

from ..storage import CorpusStorage

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""
    id: str
    type: str  # "document" or "node"
    title: str
    summary: str
    score: float
    highlights: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class SearchIndex:
    """Full-text search index for corpus content."""

    def __init__(self, storage: CorpusStorage):
        self.storage = storage
        self.index_file = storage.corpus_dir / "search_index.json"
        self._index: dict = {}
        self._documents: dict = {}

    def build(self) -> int:
        """
        Build or rebuild the search index from corpus content.
        Returns the number of items indexed.
        """
        logger.info("Building search index...")

        self._index = {}
        self._documents = {}
        indexed_count = 0

        # Index documents
        for doc in self.storage.list_documents():
            content = self.storage.get_document_content(doc.id)
            if content:
                self._index_item(
                    item_id=f"doc:{doc.id}",
                    title=doc.title,
                    content=content,
                    item_type="document",
                    metadata={
                        "source_id": doc.source_id,
                        "url": doc.url,
                        "file_path": doc.file_path
                    }
                )
                indexed_count += 1

        # Index nodes
        for node in self.storage.list_nodes():
            self._index_item(
                item_id=f"node:{node.id}",
                title=node.name,
                content=f"{node.summary}\n\n{node.content}",
                item_type="node",
                metadata={
                    "node_type": node.type.value,
                    "realm": node.attributes.realm.value if node.attributes.realm else None,
                    "rarity": node.attributes.rarity.value if node.attributes.rarity else None
                }
            )
            indexed_count += 1

        # Save index to disk
        self._save_index()
        logger.info(f"Indexed {indexed_count} items")

        return indexed_count

    def _index_item(
        self,
        item_id: str,
        title: str,
        content: str,
        item_type: str,
        metadata: dict
    ) -> None:
        """Index a single item."""
        # Store document info
        self._documents[item_id] = {
            "id": item_id,
            "type": item_type,
            "title": title,
            "content": content[:500],  # Preview
            "metadata": metadata
        }

        # Tokenize and index
        tokens = self._tokenize(f"{title} {content}")
        for token in tokens:
            if token not in self._index:
                self._index[token] = {}
            if item_id not in self._index[token]:
                self._index[token][item_id] = 0
            self._index[token][item_id] += 1

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into searchable terms."""
        # Lowercase and split on non-alphanumeric
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        # Filter very short tokens
        return [t for t in tokens if len(t) >= 2]

    def _save_index(self) -> None:
        """Save index to disk."""
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "index": self._index,
            "documents": self._documents
        }
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _load_index(self) -> bool:
        """Load index from disk. Returns True if loaded."""
        if not self.index_file.exists():
            return False
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._index = data.get("index", {})
            self._documents = data.get("documents", {})
            return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 20,
        item_type: Optional[str] = None,
        node_type: Optional[str] = None,
        realm: Optional[str] = None
    ) -> list[SearchResult]:
        """
        Search the index.

        Args:
            query: Search query string
            limit: Maximum results to return
            item_type: Filter by "document" or "node"
            node_type: Filter by node type (spell, unit, etc.)
            realm: Filter by magic realm

        Returns:
            List of SearchResult objects sorted by relevance
        """
        # Load index if not in memory
        if not self._index:
            if not self._load_index():
                self.build()

        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Score documents
        scores: dict[str, float] = {}
        for token in query_tokens:
            if token in self._index:
                for item_id, count in self._index[token].items():
                    if item_id not in scores:
                        scores[item_id] = 0
                    scores[item_id] += count

        # Build results
        results = []
        for item_id, score in sorted(scores.items(), key=lambda x: -x[1]):
            doc_info = self._documents.get(item_id)
            if not doc_info:
                continue

            # Apply filters
            if item_type and doc_info["type"] != item_type:
                continue
            if node_type and doc_info["metadata"].get("node_type") != node_type:
                continue
            if realm and doc_info["metadata"].get("realm") != realm:
                continue

            # Extract highlights
            highlights = self._extract_highlights(
                doc_info["content"],
                query_tokens
            )

            # Get real ID (strip prefix)
            real_id = item_id.split(":", 1)[1] if ":" in item_id else item_id

            results.append(SearchResult(
                id=real_id,
                type=doc_info["type"],
                title=doc_info["title"],
                summary=doc_info["content"][:200],
                score=score,
                highlights=highlights,
                metadata=doc_info["metadata"]
            ))

            if len(results) >= limit:
                break

        return results

    def _extract_highlights(self, content: str, tokens: list[str], context: int = 50) -> list[str]:
        """Extract text snippets containing search terms."""
        highlights = []
        content_lower = content.lower()

        for token in tokens[:3]:  # Max 3 highlights
            idx = content_lower.find(token)
            if idx >= 0:
                start = max(0, idx - context)
                end = min(len(content), idx + len(token) + context)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                highlights.append(snippet.strip())

        return highlights[:3]
