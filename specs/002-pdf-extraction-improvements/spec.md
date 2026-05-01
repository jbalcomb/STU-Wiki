# Feature 002: PDF Extraction Improvements

**Branch**: `002-pdf-extraction-improvements` | **Status**: in calibration | **Spec is light on purpose** — see "Process" below.

## Goal

Replace the current PDF scraper's "render the whole page as an image" behavior with text-first extraction that:

- Always recovers the actual text layer when present.
- Pulls embedded images out as separate assets, referenced inline at their position in the text.
- Filters out decorative artifacts (drop caps, ornamental flourishes) so they don't pollute the corpus.
- Falls back to a whole-page PNG only when a page has no recoverable text (image-only scans without an OCR layer).

This is the operational form of constitutional Principle VI (Extraction Fidelity), introduced alongside this feature.

## Why

The original scraper (`mom_wiki/scrapers/pdf_scraper.py`) classifies any page with an embedded image larger than ~100×100px as "image-dominant" or "mixed", then renders the *entire page* as a 2× PNG. For text PDFs that use drop caps or small ornamental images, this throws the text away and produces a corpus full of giant scanned-looking page images. Search, RAG, and any downstream NLP all break in the same way: the actual content isn't text any more, it's an image.

## Process: calibration-driven

This feature does *not* follow the usual "spec → plan → tasks → implement" Spec Kit cadence. Extraction quality is impossible to specify up-front because the right thresholds and heuristics depend on what real PDFs in the corpus look like.

Instead:

1. **Scaffold a preview tool** (`python -m mom_wiki.cli extract-preview`) that runs the new extraction logic and writes results to a temp directory *without* touching `corpus/`.
2. **Walk through real PDFs page by page** with a human reviewer. For each page, decide: is this what we want? Adjust thresholds and heuristics in `mom_wiki/scrapers/pdf_extraction.py` based on what we see.
3. **Codify findings.** Once the calibration sample feels right, fill in the rest of this spec (the chosen thresholds, the OCR decision, edge cases observed) and update `pdf_scraper.py` to call the new extraction module.
4. **Re-scrape** the existing corpus with `--force` to replace the old image-dump output with the new text-first output.

## Out of scope

- Web and LBX scrapers — they have their own (unrelated) extraction concerns.
- OCR for image-only PDFs — open question (see below); for now those pages get a fallback page render.
- Layout reconstruction (multi-column reflow, table-cell extraction) — `fitz.get_text("text")` is good enough for v1; revisit if reviewers consistently want better.

## Open questions (resolve during calibration)

- **Drop-cap / decorative threshold.** Default tentatively at 200×200px (anything smaller is filtered out). Real PDFs may push us up or down.
- **OCR fallback.** For image-only pages, do we (a) render the page as PNG and stop, or (b) run Tesseract to recover text? Option (b) costs a dependency and significant runtime; defer until a reviewer hits a PDF where it matters.
- **Image positioning.** Embedded images currently get appended at the end of each page's markdown. Should they be inline at their actual y-position? Worth it only if reviewers say the end-of-page placement is confusing.
- **Image format.** We currently re-encode everything to PNG. Some embedded JPEGs would be smaller kept as JPEG. Probably not worth the complexity unless corpus size becomes an issue.

## Test corpus

Calibration uses `data/pdf/` (gitignored). Starting set, smallest first:

- `25934_game_extra_1.pdf` (1.8 MB) — small, good for first walkthrough.
- `25935_game_extra_1.pdf` (372 KB) — even smaller; sanity check.
- `Master Of Magic - Explore And Conquer Magic Worlds The Official Strategy Guide (1994).pdf` (80 MB) — full strategy guide; the realistic target.
- `MoM_Strategy Guide_clean.pdf` (431 MB) — likely an image-only scan; will exercise the fallback path.
- `Official Strategy Guide - Explore And Conquer Magic Worlds_OCR.pdf` (203 MB) — OCR'd version of the above; should produce real text.

## Success criteria

- For text-first PDFs: extracted markdown is the actual text, with diagrams/tables/screenshots referenced inline as images. No drop caps in the image set.
- For image-only PDFs (no text layer): each page comes through as a single fallback PNG, clearly marked.
- Re-running the scraper on a previously-scraped PDF produces no diff (idempotent ingestion still works after the rewrite).
