"""Text-first PDF extraction with repetition-based decoration filtering.

Implements Principle VI (Extraction Fidelity): the text layer is primary,
embedded images are secondary, and decorative artifacts (illuminated
initials, ornaments, page borders) are filtered out before they reach the
corpus.

The decoration filter is repetition-based: any image whose object xref or
content hash appears in the document at least `repetition_threshold` times
is treated as decoration. This catches illuminated initials (the same 'T'
glyph rendered on every page that starts a paragraph with T), chapter
ornaments, recurring borders, etc. — without per-document threshold tuning.
A small `min_image_dim` floor is kept as a safety net for tiny ornaments
that somehow pass the repetition check.

The flow is:

  1. `build_catalog(pdf)` — one full pass that hashes every embedded image
     and counts its occurrences by xref and sha256.
  2. `extract_pdf(pdf, catalog=...)` — emits text + non-decorative images
     per page. If no catalog is passed, one is built internally.

Both the `extract-preview` CLI (writes to a temp dir for human review) and
the production PDF scraper (writes into the corpus) call `extract_pdf`. The
caller decides where to persist bytes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path


# An image whose xref OR sha256 appears at least this many times in the
# document is filtered out as decoration. Calibrated during feature 002.
DEFAULT_REPETITION_THRESHOLD = 3

# Safety floor: images smaller than this on either side are skipped even if
# they pass the repetition check. Catches sub-illuminated-initial ornaments
# (small flourishes, single-pixel rule lines, etc.).
DEFAULT_MIN_IMAGE_DIM = 50

# Page-render scale factor used only when a page has no text layer.
FALLBACK_RENDER_SCALE = 2


@dataclass
class CatalogedImage:
    """An image object encountered during the catalog pass.

    Stores the rendered PNG bytes and metadata so the emit pass can reuse
    them without re-decoding the same xref a second time.
    """
    xref: int
    width: int
    height: int
    ext: str
    data: bytes
    sha256: str


@dataclass
class ImageCatalog:
    """Result of the catalog pass: every unique image + occurrence counts.

    Counts are per-occurrence (each time `page.get_images()` returns the
    image counts +1), not per-page — so an illuminated 'T' that appears
    twice on one page contributes 2 to the count.
    """
    images: dict[int, CatalogedImage] = field(default_factory=dict)
    xref_count: dict[int, int] = field(default_factory=dict)
    sha256_count: dict[str, int] = field(default_factory=dict)
    total_pages: int = 0

    def is_repeating(self, xref: int, sha256: str, threshold: int) -> bool:
        """True if this image's xref OR content hash hits the threshold."""
        return (
            self.xref_count.get(xref, 0) >= threshold
            or self.sha256_count.get(sha256, 0) >= threshold
        )

    def frequency_rows(self) -> list[tuple[int, int, str, int, int]]:
        """Return rows for the catalog frequency table, most-frequent first.

        Each row: (effective_count, xref, sha256, width, height). The
        effective count is max(xref_count, sha256_count) — whichever signal
        flagged repetition.
        """
        rows = []
        for xref, info in self.images.items():
            count = max(
                self.xref_count.get(xref, 0),
                self.sha256_count.get(info.sha256, 0),
            )
            rows.append((count, xref, info.sha256, info.width, info.height))
        rows.sort(key=lambda row: (-row[0], row[1]))
        return rows


@dataclass
class ExtractedImage:
    """An image emitted into the final extraction output."""
    page: int
    index: int  # nth image on the page (0-based)
    width: int
    height: int
    ext: str
    data: bytes

    @property
    def filename(self) -> str:
        return f"page-{self.page:04d}-img-{self.index}.{self.ext}"


@dataclass
class ExtractedPage:
    """One page's worth of extracted content."""
    page_num: int
    text: str
    images: list[ExtractedImage] = field(default_factory=list)
    fallback_render: bytes | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def fallback_filename(self) -> str:
        return f"page-{self.page_num:04d}-fallback.png"

    def to_markdown(self, image_dir: str = "images") -> str:
        lines = [f"## Page {self.page_num}", ""]

        if self.fallback_render is not None:
            lines.append("_(no text layer; page rendered as image)_")
            lines.append("")
            lines.append(f"![Page {self.page_num}]({image_dir}/{self.fallback_filename})")
        else:
            if self.text:
                lines.append(self.text)
                lines.append("")
            for image in self.images:
                lines.append(
                    f"![Page {image.page} image {image.index}]"
                    f"({image_dir}/{image.filename})"
                )
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
    catalog: ImageCatalog | None = None

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


def build_catalog(file_path: Path) -> ImageCatalog:
    """First pass: walk the whole PDF, hash every embedded image, count occurrences."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("PyMuPDF not installed. Run: pip install PyMuPDF") from exc

    catalog = ImageCatalog()
    doc = fitz.open(str(file_path))
    try:
        catalog.total_pages = len(doc)

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                catalog.xref_count[xref] = catalog.xref_count.get(xref, 0) + 1

                if xref not in catalog.images:
                    cataloged = _catalog_image(doc, xref)
                    if cataloged is None:
                        continue
                    catalog.images[xref] = cataloged

                sha = catalog.images[xref].sha256
                catalog.sha256_count[sha] = catalog.sha256_count.get(sha, 0) + 1
    finally:
        doc.close()

    return catalog


def _catalog_image(doc, xref: int) -> CatalogedImage | None:
    """Decode one image by xref, return its bytes + hash, or None on failure."""
    import fitz

    try:
        pixmap = fitz.Pixmap(doc, xref)
    except Exception:
        return None

    try:
        if pixmap.colorspace and pixmap.colorspace.n > 3:
            pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
        data = pixmap.tobytes("png")
        return CatalogedImage(
            xref=xref,
            width=pixmap.width,
            height=pixmap.height,
            ext="png",
            data=data,
            sha256=hashlib.sha256(data).hexdigest(),
        )
    finally:
        pixmap = None  # release native resources


def extract_pdf(
    file_path: Path,
    page_range: tuple[int, int] | None = None,
    repetition_threshold: int = DEFAULT_REPETITION_THRESHOLD,
    min_image_dim: int = DEFAULT_MIN_IMAGE_DIM,
    catalog: ImageCatalog | None = None,
) -> ExtractionResult:
    """Extract text + non-decorative images from a PDF.

    Args:
        file_path: PDF on disk.
        page_range: 1-indexed inclusive (start, end) tuple, or None for all pages.
        repetition_threshold: images appearing >= this many times in the
            document (by xref or sha256) are filtered as decoration.
        min_image_dim: safety floor — images smaller than this on either
            side are skipped even if unique.
        catalog: pre-built ImageCatalog (e.g. from a prior `build_catalog`
            call). Built internally if None.

    Returns:
        ExtractionResult — caller decides where to persist bytes.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise ImportError("PyMuPDF not installed. Run: pip install PyMuPDF") from exc

    if catalog is None:
        catalog = build_catalog(file_path)

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
            pages.append(
                _extract_page(
                    doc,
                    page_idx,
                    catalog=catalog,
                    repetition_threshold=repetition_threshold,
                    min_image_dim=min_image_dim,
                )
            )
    finally:
        doc.close()

    return ExtractionResult(file_path=file_path, pages=pages, catalog=catalog)


def _extract_page(
    doc,
    page_idx: int,
    catalog: ImageCatalog,
    repetition_threshold: int,
    min_image_dim: int,
) -> ExtractedPage:
    """Extract a single page using the pre-built catalog for filter decisions."""
    import fitz

    page = doc[page_idx]
    page_num = page_idx + 1

    text = page.get_text("text").strip()
    images: list[ExtractedImage] = []
    notes: list[str] = []
    skipped_repeating = 0
    skipped_too_small = 0
    skipped_uncatalogued = 0

    for img_index, img_info in enumerate(page.get_images(full=True)):
        xref = img_info[0]
        cataloged = catalog.images.get(xref)
        if cataloged is None:
            skipped_uncatalogued += 1
            continue

        if cataloged.width < min_image_dim or cataloged.height < min_image_dim:
            skipped_too_small += 1
            continue

        if catalog.is_repeating(xref, cataloged.sha256, repetition_threshold):
            skipped_repeating += 1
            continue

        images.append(ExtractedImage(
            page=page_num,
            index=img_index,
            width=cataloged.width,
            height=cataloged.height,
            ext=cataloged.ext,
            data=cataloged.data,
        ))

    if skipped_repeating:
        notes.append(
            f"filtered {skipped_repeating} repeating image(s) "
            f"(threshold={repetition_threshold} occurrences)"
        )
    if skipped_too_small:
        notes.append(f"skipped {skipped_too_small} sub-{min_image_dim}px image(s)")
    if skipped_uncatalogued:
        notes.append(f"{skipped_uncatalogued} image(s) failed to decode during catalog pass")

    fallback_render: bytes | None = None
    if not text:
        # Last resort per Principle VI: page has no recoverable text layer.
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


def format_catalog_table(catalog: ImageCatalog, top: int | None = None) -> str:
    """Format the catalog frequency table for human eyeballing.

    `top` limits the output to the N most frequent images; None shows all.
    """
    rows = catalog.frequency_rows()
    if top is not None:
        rows = rows[:top]

    lines = [
        f"Total pages:         {catalog.total_pages}",
        f"Unique image xrefs:  {len(catalog.images)}",
        f"Unique image sha256: {len(catalog.sha256_count)}",
        "",
        f"{'COUNT':>6}  {'XREF':>6}  {'SHA256 (16)':<16}  {'SIZE':>11}",
        "-" * 50,
    ]
    for count, xref, sha, width, height in rows:
        size = f"{width}x{height}"
        lines.append(f"{count:>6}  {xref:>6}  {sha[:16]:<16}  {size:>11}")
    return "\n".join(lines)
