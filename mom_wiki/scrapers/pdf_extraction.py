"""Text-first PDF extraction.

Implements Principle VI (Extraction Fidelity): pull the text layer first,
extract embedded images as their own assets referenced inline, filter out
decorative artifacts (drop caps, flourishes) by minimum dimension, and only
fall back to a whole-page render when a page has no recoverable text at all.

This module is consumed by both the `extract-preview` CLI (which writes to
a temp directory for human review) and the real PDF scraper (which writes
into the corpus). Both call `extract_pdf()` and decide independently where
to persist the bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


# Minimum dimension (in pixels) for an embedded image to be considered a
# "real" asset. Images smaller than this on either side are treated as
# decorative (drop caps, ornaments, page borders) and skipped. Calibrated
# during feature 002; adjust based on real PDFs.
DEFAULT_MIN_IMAGE_DIM = 200

# Page-render scale factor used only when a page has no text layer.
FALLBACK_RENDER_SCALE = 2


@dataclass
class ExtractedImage:
    """An image pulled out of a PDF page."""
    page: int
    index: int  # nth image on the page (0-based)
    width: int
    height: int
    ext: str  # "png", "jpeg", etc.
    data: bytes

    @property
    def filename(self) -> str:
        return f"page-{self.page:04d}-img-{self.index}.{self.ext}"


@dataclass
class ExtractedPage:
    """One page's worth of extracted content."""
    page_num: int
    text: str  # the recovered text layer (may be empty)
    images: list[ExtractedImage] = field(default_factory=list)
    fallback_render: bytes | None = None  # full-page PNG when text is empty
    notes: list[str] = field(default_factory=list)

    @property
    def fallback_filename(self) -> str:
        return f"page-{self.page_num:04d}-fallback.png"

    def to_markdown(self, image_dir: str = "images") -> str:
        """Render this page to markdown, referencing images at `image_dir/`."""
        lines = [f"## Page {self.page_num}", ""]

        if self.fallback_render is not None:
            lines.append(f"_(no text layer; page rendered as image)_")
            lines.append("")
            lines.append(f"![Page {self.page_num}]({image_dir}/{self.fallback_filename})")
        else:
            if self.text:
                lines.append(self.text)
                lines.append("")
            for image in self.images:
                lines.append(f"![Page {image.page} image {image.index}]({image_dir}/{image.filename})")
                lines.append("")

        if self.notes:
            lines.append("")
            lines.append(f"<!-- extraction notes: {'; '.join(self.notes)} -->")

        return "\n".join(lines).rstrip() + "\n"


@dataclass
class ExtractionResult:
    """Everything pulled from a single PDF."""
    file_path: Path
    pages: list[ExtractedPage] = field(default_factory=list)

    @property
    def total_images(self) -> int:
        return sum(len(p.images) for p in self.pages)

    @property
    def total_fallbacks(self) -> int:
        return sum(1 for p in self.pages if p.fallback_render is not None)

    def to_markdown(self, image_dir: str = "images") -> str:
        title = self.file_path.stem.replace("_", " ").replace("-", " ").strip()
        body = "\n".join(p.to_markdown(image_dir=image_dir) for p in self.pages)
        return f"# {title}\n\n{body}"


def extract_pdf(
    file_path: Path,
    page_range: tuple[int, int] | None = None,
    min_image_dim: int = DEFAULT_MIN_IMAGE_DIM,
) -> ExtractionResult:
    """Extract text + significant images from a PDF.

    Args:
        file_path: PDF on disk.
        page_range: 1-indexed inclusive (start, end) tuple, or None for all pages.
        min_image_dim: minimum width OR height for an embedded image to be
            treated as a real asset rather than decorative.

    Returns:
        ExtractionResult — caller decides where to write text + image bytes.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("PyMuPDF not installed. Run: pip install PyMuPDF") from exc

    doc = fitz.open(str(file_path))
    try:
        total_pages = len(doc)
        if page_range is None:
            start, end = 1, total_pages
        else:
            start = max(1, page_range[0])
            end = min(total_pages, page_range[1])

        pages: list[ExtractedPage] = []
        for page_idx in range(start - 1, end):
            pages.append(_extract_page(doc, page_idx, min_image_dim=min_image_dim))
    finally:
        doc.close()

    return ExtractionResult(file_path=file_path, pages=pages)


def _extract_page(doc, page_idx: int, min_image_dim: int) -> ExtractedPage:
    """Extract a single page. `doc` is an open fitz.Document."""
    import fitz

    page = doc[page_idx]
    page_num = page_idx + 1

    text = page.get_text("text").strip()
    images: list[ExtractedImage] = []
    notes: list[str] = []
    skipped_decorative = 0

    for img_index, img_info in enumerate(page.get_images(full=True)):
        xref = img_info[0]
        try:
            pixmap = fitz.Pixmap(doc, xref)
        except Exception as exc:
            notes.append(f"image xref={xref} unreadable: {exc}")
            continue

        try:
            if pixmap.width < min_image_dim or pixmap.height < min_image_dim:
                skipped_decorative += 1
                continue

            # CMYK / extra-channel images need conversion before PNG encoding.
            if pixmap.colorspace and pixmap.colorspace.n > 3:
                pixmap = fitz.Pixmap(fitz.csRGB, pixmap)

            images.append(ExtractedImage(
                page=page_num,
                index=img_index,
                width=pixmap.width,
                height=pixmap.height,
                ext="png",
                data=pixmap.tobytes("png"),
            ))
        finally:
            pixmap = None  # release native resources

    if skipped_decorative:
        notes.append(
            f"skipped {skipped_decorative} sub-{min_image_dim}px image(s) as decorative"
        )

    fallback_render: bytes | None = None
    if not text:
        # No text layer — render the whole page as a fallback so the content
        # isn't lost. Per Principle VI this is a last resort, not the default.
        matrix = fitz.Matrix(FALLBACK_RENDER_SCALE, FALLBACK_RENDER_SCALE)
        page_pixmap = page.get_pixmap(matrix=matrix)
        try:
            fallback_render = page_pixmap.tobytes("png")
        finally:
            page_pixmap = None
        notes.append("no text layer recovered — fallback page render emitted")

    return ExtractedPage(
        page_num=page_num,
        text=text,
        images=images,
        fallback_render=fallback_render,
        notes=notes,
    )


def write_extraction(
    result: ExtractionResult,
    output_dir: Path,
    image_subdir: str = "images",
) -> tuple[Path, Path]:
    """Persist an ExtractionResult to disk: markdown + images.

    Returns (markdown_path, images_dir).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / image_subdir
    images_dir.mkdir(parents=True, exist_ok=True)

    for page in result.pages:
        for image in page.images:
            (images_dir / image.filename).write_bytes(image.data)
        if page.fallback_render is not None:
            (images_dir / page.fallback_filename).write_bytes(page.fallback_render)

    markdown_path = output_dir / "preview.md"
    markdown_path.write_text(result.to_markdown(image_dir=image_subdir), encoding="utf-8")

    return markdown_path, images_dir
