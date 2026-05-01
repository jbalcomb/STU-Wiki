"""Abstract base scraper class."""

from abc import ABC, abstractmethod
from typing import Generator
import logging

from ..models import Source, Document, Node, ScrapeJob
from ..storage import CorpusStorage

logger = logging.getLogger(__name__)


class ScrapedContent:
    """Container for scraped content before storage."""

    def __init__(
        self,
        title: str,
        content: str,
        url: str | None = None,
        file_path: str | None = None,
        metadata: dict | None = None,
        nodes: list[Node] | None = None
    ):
        self.title = title
        self.content = content
        self.url = url
        self.file_path = file_path
        self.metadata = metadata or {}
        self.nodes = nodes or []


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, storage: CorpusStorage):
        self.storage = storage
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def scrape(self, source: Source) -> Generator[ScrapedContent, None, None]:
        """
        Scrape content from the source.
        Yields ScrapedContent objects for each piece of content.
        """
        pass

    @abstractmethod
    def can_handle(self, source: Source) -> bool:
        """Check if this scraper can handle the given source."""
        pass

    def process_source(self, source: Source, job: ScrapeJob | None = None) -> dict:
        """
        Process a source and store results.
        Implements idempotent ingestion via checksum comparison.

        Returns a summary dict with counts and status.
        """
        self.logger.info(f"Processing source: {source.name} ({source.location})")

        # Create job if not provided
        if job is None:
            job = ScrapeJob(source_id=source.id)
            self.storage.create_job(job)

        try:
            for scraped in self.scrape(source):
                # Compute checksum for dedup
                checksum = self.storage.compute_checksum(scraped.content)

                # Check if content already exists (idempotent)
                existing = self.storage.get_document_by_checksum(source.id, checksum)
                if existing:
                    job.documents_unchanged += 1
                    self.logger.debug(f"Unchanged: {scraped.title}")
                    continue

                # Create document
                document = Document(
                    source_id=source.id,
                    title=scraped.title,
                    content_path="",  # Will be set by save_document
                    url=scraped.url,
                    file_path=scraped.file_path,
                    checksum=checksum,
                )

                # Add metadata
                if scraped.metadata:
                    document.metadata.tags = scraped.metadata.get("tags", [])
                    document.metadata.author = scraped.metadata.get("author")
                    document.metadata.publish_date = scraped.metadata.get("publish_date")
                    document.metadata.custom = scraped.metadata.get("custom", {})

                # Save document and content
                is_new = self.storage.save_document(document, scraped.content)

                if is_new:
                    job.documents_created += 1
                    self.logger.info(f"Created: {scraped.title}")
                else:
                    job.documents_updated += 1
                    self.logger.info(f"Updated: {scraped.title}")

                # Create/update nodes
                for node in scraped.nodes:
                    existing_node = self.storage.get_node_by_name(node.name, node.type.value)
                    if existing_node:
                        existing_node.add_document(document.id)
                        existing_node.update_content(node.content, node.summary)
                        self.storage.update_node(existing_node)
                    else:
                        node.add_document(document.id)
                        self.storage.create_node(node)
                        job.nodes_created.append(node.id)

                    # Link document to node
                    document.add_node(node.id)

            job.complete(success=True)
            source.mark_success()

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error scraping {source.name}: {error_msg}")
            job.add_error(error_msg)
            job.complete(success=False)
            source.mark_failed(error_msg)

        self.storage.update_job(job)
        self.storage.update_source(source)

        return {
            "job_id": job.id,
            "status": job.status.value,
            "documents_created": job.documents_created,
            "documents_updated": job.documents_updated,
            "documents_unchanged": job.documents_unchanged,
            "nodes_created": len(job.nodes_created),
            "errors": job.errors
        }
