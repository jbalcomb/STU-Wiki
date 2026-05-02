"""Regenerate the golden-file fixtures used by the integration tests.

Run this whenever you intentionally change extraction behavior:

    python tests/python/fixtures/pdf_extraction/regen.py

This writes:

  - page-NNNN.expected.md   — committed; the human-blessed expected output
  - images/                 — gitignored; local-only fixture images so the
                              .expected.md files render with images in your
                              markdown previewer

The images come from the test PDF (data/pdf/25934_game_extra_1.pdf) which
is itself gitignored. They're regenerable on demand and should not land in
the public repo.

REVIEW BEFORE TRUSTING: regenerated .expected.md files are a *draft* of
what the extractor currently produces, not a contract for what's correct.
Eyeball the diff against your previous fixtures and edit by hand before
treating them as the new ground truth.
"""

from pathlib import Path

from mom_wiki.scrapers.pdf_extraction import build_catalog, extract_pdf, write_extraction


PDF_PATH = Path("data/pdf/25934_game_extra_1.pdf")
PAGES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13)
OUTPUT_DIR = Path(__file__).parent


def main() -> int:
    if not PDF_PATH.exists():
        print(f"ERROR: test PDF not found at {PDF_PATH}")
        return 1

    images_dir = OUTPUT_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    catalog = build_catalog(PDF_PATH)
    for page_num in PAGES:
        result = extract_pdf(PDF_PATH, page_range=(page_num, page_num), catalog=catalog)
        page = result.pages[0]
        markdown = page.to_markdown()
        fixture_path = OUTPUT_DIR / f"page-{page_num:04d}.expected.md"
        fixture_path.write_text(markdown, encoding="utf-8")
        # Also write any images this page references, so the .md previews.
        for image in page.images:
            (images_dir / image.filename).write_bytes(image.data)
        if page.fallback_render is not None:
            (images_dir / page.fallback_filename).write_bytes(page.fallback_render)
        if page.title_art is not None:
            (images_dir / page.title_art.filename).write_bytes(page.title_art.data)
        print(f"wrote {fixture_path} ({len(markdown)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
