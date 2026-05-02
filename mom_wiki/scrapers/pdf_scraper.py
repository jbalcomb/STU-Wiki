"""PDF scraper backed by mom_wiki.scrapers.pdf_extraction.

The previous implementation classified pages as text/image/mixed and rendered
the entire page as a 2× PNG whenever an embedded image (even a small drop
cap) tripped the threshold — turning text-heavy pages into image dumps.
This file is now a thin adapter around the new text-first extraction module
(see specs/002-pdf-extraction-improvements/spec.md and Principle VI).
"""

from pathlib import Path
from typing import Generator
import logging

from ..models import Source, SourceType, Node, NodeType
from .base import BaseScraper, ScrapedContent
from .pdf_extraction import build_catalog, extract_pdf

logger = logging.getLogger(__name__)


class PDFScraper(BaseScraper):
    """Scraper for PDF documents using the text-first extraction module."""

    def __init__(self, storage):
        super().__init__(storage)
        self.images_dir = Path(storage.base_dir) / "corpus" / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def can_handle(self, source: Source) -> bool:
        return source.type == SourceType.PDF

    def scrape(self, source: Source) -> Generator[ScrapedContent, None, None]:
        """Extract text + non-decorative images from a PDF, yielding one
        ScrapedContent per file.

        Idempotent ingestion (per feature 001) keys documents by
        (source_id, file_path), so re-scraping the same PDF updates the
        existing document in place rather than creating a new UUID.
        """
        file_path = Path(source.location)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            catalog = build_catalog(file_path)
            result = extract_pdf(file_path, catalog=catalog)
        except Exception as exc:
            logger.error(f"Failed to extract PDF {file_path}: {exc}")
            raise

        # Persist images, fallback renders, and title-art renders into the
        # corpus's shared images directory. The markdown emitted below
        # references them with paths relative to the markdown file's
        # location (corpus/content/<id>.md → ../images/<filename>).
        title_art_count = 0
        for page in result.pages:
            for image in page.images:
                (self.images_dir / image.filename).write_bytes(image.data)
            if page.fallback_render is not None:
                (self.images_dir / page.fallback_filename).write_bytes(page.fallback_render)
            if page.title_art is not None:
                (self.images_dir / page.title_art.filename).write_bytes(page.title_art.data)
                title_art_count += 1

        markdown = result.to_markdown(image_dir="../images")
        if not markdown.strip():
            logger.warning(f"No content extracted from {file_path}")
            return

        title = file_path.stem.replace("_", " ").replace("-", " ").title()

        node = Node(
            type=NodeType.PAGE,
            name=title,
            summary=f"PDF document: {file_path.name}",
            content=markdown[:1000],
        )

        yield ScrapedContent(
            title=title,
            content=markdown,
            file_path=str(file_path),
            metadata={
                "source_type": "pdf",
                "page_count": len(result.pages),
                "image_count": result.total_images,
                "fallback_render_count": result.total_fallbacks,
                "title_art_count": title_art_count,
            },
            nodes=[node],
        )

    def extract_toc(self, file_path: str) -> list[dict]:
        """Extract table of contents from PDF."""
        try:
            import fitz
            doc = fitz.open(file_path)
            toc = doc.get_toc()
            doc.close()

            return [
                {"level": level, "title": title, "page": page}
                for level, title, page in toc
            ]
        except Exception as e:
            logger.error(f"Failed to extract TOC: {e}")
            return []
