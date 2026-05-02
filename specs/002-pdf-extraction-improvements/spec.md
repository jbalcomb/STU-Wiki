# Feature 002: PDF Extraction Improvements

**Branch**: `002-pdf-extraction-improvements` | **Status**: calibrated; production wiring + ship pending.

## Goal

Replace the original PDF scraper's "render the whole page as an image" behavior with text-first extraction that:

- Recovers the actual text layer when present, including illuminated initials that PyMuPDF emits as separate text blocks.
- Pulls embedded images out as their own assets, referenced inline in markdown.
- Filters decorative artifacts (drop caps, ornaments, repeating page borders) so they don't pollute the corpus.
- Renders stylized title-art regions (chapter openers, cover pages) as a single composite image with alt text instead of emitting their components as scrambled text fragments.
- Falls back to a whole-page PNG only when a page has no recoverable text layer.

This is the operational form of constitutional Principle VI (Extraction Fidelity), introduced alongside this feature.

## Why

The original scraper (`mom_wiki/scrapers/pdf_scraper.py`) classifies any page with an embedded image larger than ~100×100px as "image-dominant" or "mixed", then renders the *entire page* as a 2× PNG. For text PDFs that use drop caps or small ornamental images, this throws the text away and produces a corpus full of giant scanned-looking page images. Search, RAG, and any downstream NLP all break in the same way: the actual content isn't text any more, it's an image.

## Process: calibration-driven

This feature did not follow the usual "spec → plan → tasks → implement" Spec Kit cadence. Extraction quality is impossible to specify up-front because the right thresholds and heuristics depend on what real PDFs look like.

What actually happened:

1. **Scaffolded a preview tool** (`python -m mom_wiki.cli extract-preview`) that runs the new extraction logic into a temp directory without touching `corpus/`. Added `--catalog` and `--debug-page` modes for inspection.
2. **Walked through `data/pdf/25934_game_extra_1.pdf` page by page** with a human reviewer, surfaced specific problems (illuminated 'I' on page 9, word-per-line wrap on page 13, title art on pages 1 and 5, page-footer leaks), and adjusted heuristics until each was right.
3. **Codified the findings** into `mom_wiki/scrapers/pdf_extraction.py` and tests under `tests/python/`.
4. **Wire `pdf_scraper.py`** to call the new module so production scrapes (`python -m mom_wiki.cli scrape`) get the new behavior.
5. **Re-scrape** any previously-scraped PDF sources with `--force` to replace old image-dump output.

## Resolved decisions

The four open questions from the original spec, after calibration:

- **Decorative artifact filtering — repetition, not size.** The size threshold idea (200×200px floor) didn't survive contact with real data. The decisive signal is *repetition*: an illuminated initial 'T' image is reused on every paragraph that starts with T, but a real diagram appears once. Implementation: two-pass extraction. Pass 1 (`build_catalog`) hashes every embedded image (sha256) and counts occurrences by xref *and* content hash. Pass 2 (`extract_pdf`) skips any image whose xref or hash hits `repetition_threshold` (default 3). A small `min_image_dim=50` size floor is kept as a safety net for sub-illuminated-initial ornaments. This generalizes beyond drop caps to chapter ornaments, dividers, page borders, and recurring header/footer artwork — for free.
- **OCR fallback — yes, optional, via Tesseract.** Added `pytesseract` + `Pillow` as soft dependencies. The Tesseract binary itself is a separate user install (`winget install UB-Mannheim.TesseractOCR` on Windows). The code probes for the binary on PATH and at the standard Windows install path; if it can't be found, OCR silently degrades to text-block-only alt text. Used for title-art alt text with `--psm 6` (single uniform block). Text-block alt is preferred when substantive (≥8 chars) — for stylized title typography, OCR mangles letterforms and text blocks usually win on quality.
- **Image positioning — end-of-page for now.** Embedded images are emitted at the end of each page's markdown. Mid-paragraph positioning (interleaving by reading order) is deferred. Title-art is placed at the top of the page since it's a header asset by definition.
- **Image format — re-encoded to PNG everywhere.** No corpus size pressure yet, and uniform format simplifies downstream tooling.

## What we learned

Non-obvious findings worth keeping in the spec:

- **Illuminated initials in the test corpus are font-based, not raster.** PyMuPDF's `page.get_text("blocks")` exposes them as a separate text block in a decorative font (`DorovarFLF-Carolus`) positioned to the left of the body text, vertically overlapping the start of the paragraph. Recovery is layout reassembly, not OCR — `_assemble_page_text` matches initials to body blocks by y-overlap and prepends them.
- **Word-per-line wrap in justified text around images.** When body text wraps tightly around a portrait image, PyMuPDF emits each word as a separate showtext op surfaced as `\n` inside a single block. `_normalize_block_text` collapses those soft breaks while preserving bullet-list structure (a line containing only a bullet character starts a new bullet item).
- **Title-art is a composite, not a single object.** Pages 1 and 5 of the test PDF combine an embedded JPEG, ~226 vector drawing operations, and three small decorative text blocks. None of these alone is the visual asset; the asset is what `page.get_pixmap(clip=...)` renders over that whole region. Detection: drawings *above* the body anchor (topmost paragraph-length block, ≥40 chars), with a y-gap heuristic to drop stragglers that would otherwise pull the clip rect down over body headings.
- **Vector-drawn typography is unrecoverable as text.** The word "Magic" in "Master of Magic" on the title pages is rendered as filled vector primitives, not as a text glyph. It's not in `get_text()`, it's not in `get_drawings()` as a recognizable letter, and Tesseract on the rendered region produces mangled output. Treated as a curation gap: the human edits the alt text by hand if the literal word matters.
- **Raw drawing counts mislead.** Page 9 reports 13 drawings but the visually salient elements are just the illuminated 'I' (5 ops), the screenshot's frame (3 ops), and full-page chrome (5 ops). Title-art detection needs to filter chrome (drawings spanning >80% of page width or height, or extending off-page) before counting.
- **Markdown `\n` is a soft break.** Single-newline-separated lines render correctly when the markdown viewer respects CommonMark. So `• item 1\n• item 2` works as a list. We use `  \n` between consecutive bullet items for tighter rendering, and `\n\n` only between distinct paragraphs.

## Curation gaps (extractor cannot produce; human edits in)

These showed up during fixture review and are deliberately out of scope for the extractor:

- **`## H2` / `### H3` heading detection.** Distinguishing "this ALL-CAPS line is a section heading" from "this ALL-CAPS line is an inline label" requires document-level context the extractor doesn't have. Even font analysis only narrows it; there's a final editorial call.
- **Manual alt text for vector-only typography** (e.g. the missing "Magic" in title-page alt text).
- **Sentence-boundary `\n` preservation inside a single PDF block.** When a block contains "...subject.\nThere are five types..." the human sometimes wants the newline kept (logical break) and sometimes wants it collapsed (soft wrap). Heuristics over-trigger; human judges per case.
- **HTML annotation comments** like `<!-- PICTURE IS WRONG -->` for editorial notes.
- **Title-page rewrite.** On pages 1 and 5, the human chooses to drop the stylized title text entirely and keep just the rendered image with manually-written alt text. The extractor produces both image and text; the human prunes.

These gaps are encoded in the integration test suite as `@pytest.mark.xfail(strict=True)` with focused reason notes — the tests fail loudly if the extractor accidentally starts producing the curated form, prompting a review.

## Out of scope

- Web and LBX scrapers — their extraction concerns are unrelated.
- OCR for image-only PDFs (no text layer at all). Currently those pages get a fallback page render with a "no text layer" note in `ExtractedPage.notes`. Worth revisiting if the corpus grows to include sources that need it.
- Layout reconstruction (multi-column reflow, table-cell extraction). `fitz.get_text("blocks")` plus our reassembly is good enough for v1; revisit if reviewers consistently want better.
- Mid-paragraph image positioning by reading order.

## Test corpus

Calibration uses `data/pdf/` (gitignored). The small file is the calibration target — the larger strategy guides aren't more meaningful for this feature, just bigger.

- `25934_game_extra_1.pdf` (1.8 MB) — primary calibration sample. Has the full pattern set: illuminated initials, bulleted lists, screenshots in body, title-art on pages 1 and 5, image-only fallback page (page 4).

The bigger PDFs in `data/pdf/` (the 80MB / 200MB / 431MB strategy-guide files) aren't the natural focus. The corpus's high-value content is the community web sources (fandom wiki, realms-beyond) and usenet archives — those are separate scrapers (web, future) and don't share extraction concerns with PDF.

## Success criteria

- ✅ Text-first PDFs: markdown is the actual text, diagrams/screenshots referenced inline, decoration filtered. Verified via `tests/python/integration/test_pdf_extraction_golden.py`.
- ✅ Illuminated initials: recovered as the leading character of their paragraph (`If you choose...` on page 9, `Ariel is a high priestess...` on page 13's bullet list).
- ✅ Title-art: rendered as one composite asset with alt text on pages 1 and 5; no false positives on pages 2–13.
- ✅ Image-only pages: produce a single fallback PNG with a clearly-marked extraction note (page 4).
- ✅ Idempotent ingestion: re-running the scraper on a previously-scraped PDF should produce no diff. (Inherited from feature 001's fix; verified on storage-layer tests.)
- ⏳ Production wiring: `mom_wiki/scrapers/pdf_scraper.py` calls `pdf_extraction.extract_pdf`, so `python -m mom_wiki.cli scrape` produces the new output. *Pending in this PR.*
