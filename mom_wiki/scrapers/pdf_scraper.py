"""PDF scraper using PyMuPDF."""

from pathlib import Path
from typing import Generator
import logging

from ..models import Source, SourceType, Node, NodeType
from .base import BaseScraper, ScrapedContent

logger = logging.getLogger(__name__)

# Page classification thresholds
MIN_TEXT_CHARS = 100  # Pages with less text are considered image-dominant
MIN_IMAGE_SIZE = 10000  # Minimum pixel area (width * height) to count as significant


class PageType:
    """Page classification types."""
    TEXT = "text"
    IMAGE = "image"
    MIXED = "mixed"


class PDFScraper(BaseScraper):
    """Scraper for PDF documents using PyMuPDF (fitz)."""

    def __init__(self, storage):
        super().__init__(storage)
        self.images_dir = Path(storage.base_dir) / "corpus" / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def can_handle(self, source: Source) -> bool:
        """Check if this scraper can handle the source."""
        return source.type == SourceType.PDF

    def scrape(self, source: Source) -> Generator[ScrapedContent, None, None]:
        """Extract text and images from a PDF file."""
        file_path = Path(source.location)

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF not installed. Run: pip install PyMuPDF")

        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            raise

        # Generate a document ID for image naming
        doc_id = file_path.stem

        # Process each page
        content_parts = []
        page_metadata = []
        images_extracted = 0

        for page_num, page in enumerate(doc, start=1):
            page_content, page_info = self._process_page(
                doc, page, page_num, doc_id
            )
            if page_content:
                content_parts.append(page_content)
                page_metadata.append(page_info)
                if page_info.get("has_image"):
                    images_extracted += 1

        content = "\n\n".join(content_parts)
        doc.close()

        if not content.strip():
            logger.warning(f"No content extracted from {file_path}")
            return

        # Create title from filename
        title = file_path.stem.replace("_", " ").replace("-", " ").title()

        # Create a page-type node
        node = Node(
            type=NodeType.PAGE,
            name=title,
            summary=f"PDF document: {file_path.name}",
            content=content[:1000]  # First 1000 chars as content preview
        )

        yield ScrapedContent(
            title=title,
            content=content,
            file_path=str(file_path),
            metadata={
                "source_type": "pdf",
                "page_count": len(content_parts),
                "images_extracted": images_extracted,
                "pages": page_metadata,
            },
            nodes=[node]
        )

    def _process_page(self, doc, page, page_num: int, doc_id: str) -> tuple[str, dict]:
        """Process a single page and return content and metadata."""
        import fitz

        text = page.get_text("text").strip()
        images = page.get_images()

        # Classify the page
        page_type = self._classify_page(text, images)

        page_info = {
            "page": page_num,
            "type": page_type,
            "text_length": len(text),
            "image_count": len(images),
            "has_image": False,
        }

        # Build content based on page type
        if page_type == PageType.TEXT:
            # Text-only page
            content = f"## Page {page_num}\n\n{text}"

        elif page_type == PageType.IMAGE:
            # Image-dominant page - extract and save the image
            image_path = self._extract_page_image(doc, page, page_num, doc_id)
            if image_path:
                page_info["has_image"] = True
                page_info["image_path"] = str(image_path)
                # Include any text as a caption/title
                caption = text if text else f"Page {page_num}"
                content = f"## Page {page_num}\n\n![{caption}]({image_path})"
            else:
                # Fallback to text if image extraction fails
                content = f"## Page {page_num}\n\n{text}" if text else ""

        else:  # MIXED
            # Both text and images - extract image and include text
            image_path = self._extract_page_image(doc, page, page_num, doc_id)
            if image_path:
                page_info["has_image"] = True
                page_info["image_path"] = str(image_path)
                content = f"## Page {page_num}\n\n![Page {page_num} Image]({image_path})\n\n{text}"
            else:
                content = f"## Page {page_num}\n\n{text}"

        return content, page_info

    def _classify_page(self, text: str, images: list) -> str:
        """Classify a page as text, image, or mixed."""
        has_significant_text = len(text) >= MIN_TEXT_CHARS
        has_significant_image = any(
            img[2] * img[3] >= MIN_IMAGE_SIZE for img in images
        ) if images else False

        if has_significant_text and has_significant_image:
            return PageType.MIXED
        elif has_significant_image:
            return PageType.IMAGE
        else:
            return PageType.TEXT

    def _extract_page_image(self, doc, page, page_num: int, doc_id: str) -> str | None:
        """Extract the page as an image and save it."""
        try:
            import fitz

            # Render page to a pixmap (image)
            # Use a reasonable resolution (2x for clarity)
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)

            # Save as PNG
            image_filename = f"{doc_id}-page-{page_num}.png"
            image_path = self.images_dir / image_filename
            pix.save(str(image_path))

            logger.info(f"Extracted image: {image_filename}")

            # Return relative path for markdown reference
            return f"images/{image_filename}"

        except Exception as e:
            logger.error(f"Failed to extract image from page {page_num}: {e}")
            return None

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
