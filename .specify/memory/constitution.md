# SimTexWiki Constitution

## Core Principles

### I. Unified Content Model

All scraped content (web pages, PDFs, binary files) normalizes to a common document schema with: source URL/path, extraction timestamp, content type, raw text, and structured metadata.

### II. Scraper Isolation

Each scraper type (web, PDF, binary) is a standalone module with its own parser. Scrapers output the unified content model. Adding a new source type requires only a new scraper module.

### III. Idempotent Ingestion

Re-scraping the same source updates existing records rather than creating duplicates. Content is keyed by source identifier. Ingestion is resumable after failures.

### IV. Source Attribution

Every piece of content maintains provenance: original source, scrape date, and transformation history. Users can trace any wiki content back to its origin.

### V. Plain Text Priority

Store extracted text in plain/markdown format for searchability. Binary artifacts (images, attachments) stored separately with references. Full-text search is a first-class feature.

### VI. Extraction Fidelity

Extracted text is the primary representation of every source. Binary assets (figures, diagrams, tables, scans) are secondary — attached with provenance and referenced inline at their position in the text. Whole-page or whole-document renderings are a last-resort fallback, used only when no text can be recovered (e.g. an image-only PDF without an OCR layer); they are never the default. Decorative artifacts (drop caps, ornamental flourishes, page borders) are not assets — extractors must filter them out by size or other heuristic so they do not pollute the corpus.

## Data Sources

- **Web**: HTML pages via HTTP/HTTPS
- **PDF**: Text extraction from PDF documents
- **Binary**: Structured data files (game data, configs, serialized formats)

## Governance

Constitution changes require updating this file and notifying collaborators.

**Version**: 1.1.0 | **Ratified**: 2026-04-16 | **Last Amended**: 2026-05-01
