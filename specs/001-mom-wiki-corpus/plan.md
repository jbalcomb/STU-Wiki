# Implementation Plan: Master of Magic Wiki Corpus

**Branch**: `001-mom-wiki-corpus` | **Date**: 2026-04-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-mom-wiki-corpus/spec.md`

## Summary

Build a knowledge corpus for Master of Magic (1994 game) with multi-source scraping (web, PDF, LBX binary files), text-file storage on GitHub with Google Drive for large binaries, REST API, MCP wrapper for AI agent RAG, and 3D graph visualization. Python for local tools/API, JavaScript for web frontend, no database.

## Technical Context

**Language/Version**: Python 3.11+ (scrapers, API, MCP server), JavaScript ES2022+ (frontend)
**Primary Dependencies**:
- Python: FastAPI, requests, BeautifulSoup4, PyMuPDF, google-api-python-client, mcp-sdk
- JavaScript: Three.js/Force-Graph-3D, Lunr.js
**Storage**: JSON files + Markdown files (no database)
**Testing**: pytest (Python), Jest (JavaScript)
**Target Platform**: Local CLI + GitHub Pages (static site) + MCP server
**Project Type**: Multi-component: CLI tool + REST API + MCP server + static web app
**Performance Goals**: Search <2s, 3D graph 1000 nodes @ 60fps
**Constraints**: GitHub file size limits (100MB), Google Drive for large files
**Scale/Scope**: ~1000-2000 nodes, ~500 documents, single admin user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Unified Content Model | ✅ PASS | All content normalizes to Document/Node schema |
| II. Scraper Isolation | ✅ PASS | Separate modules: web_scraper, pdf_scraper, lbx_scraper |
| III. Idempotent Ingestion | ✅ PASS | Checksum-based dedup, update-not-create on re-scrape |
| IV. Source Attribution | ✅ PASS | Document.source_id, url, drive_url fields preserved |
| V. Plain Text Priority | ✅ PASS | Markdown for content, JSON for metadata, binaries in Drive |

**Gate Result**: PASS - All constitution principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/001-mom-wiki-corpus/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── rest-api.md
│   └── mcp-server.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
mom_wiki/                    # Python package
├── __init__.py
├── cli.py                   # CLI entry point
├── models/                  # Data models (Pydantic)
│   ├── __init__.py
│   ├── source.py
│   ├── document.py
│   ├── node.py
│   └── relationship.py
├── scrapers/                # Isolated scraper modules
│   ├── __init__.py
│   ├── base.py              # Abstract scraper interface
│   ├── web_scraper.py
│   ├── pdf_scraper.py
│   └── lbx_scraper.py       # MoM binary parser
├── storage/                 # File-based storage
│   ├── __init__.py
│   ├── corpus.py            # JSON/Markdown file operations
│   └── drive.py             # Google Drive integration
├── search/                  # Search index
│   ├── __init__.py
│   └── indexer.py
├── api/                     # REST API
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   └── routes/
│       ├── search.py
│       ├── documents.py
│       ├── nodes.py
│       └── sources.py
└── mcp_server/              # MCP server
    ├── __init__.py
    └── server.py

frontend/                    # JavaScript static site
├── package.json
├── src/
│   ├── index.html
│   ├── main.js              # Entry point
│   ├── graph.js             # 3D graph (Force-Graph)
│   ├── search.js            # Client-side search (Lunr.js)
│   └── api.js               # REST API client
├── public/
│   └── assets/
└── dist/                    # Build output for GitHub Pages

corpus/                      # Scraped data (generated)
├── documents/
├── content/
├── nodes/
├── jobs/
├── relationships.json
└── search-index.json

data/                        # Source files (local)
├── lbx/                     # MoM LBX files
└── pdf/                     # PDF documents

config/
├── google-credentials.json  # Drive API credentials (gitignored)
└── settings.json            # Runtime settings

tests/
├── python/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
└── javascript/
    └── graph.test.js

docs/                        # GitHub Pages assets
├── index.html               # Redirect or landing
├── stats.svg                # Animated stats badge
└── CNAME                    # Custom domain (if any)

sources.json                 # Configured sources
requirements.txt             # Python dependencies
.github/
└── workflows/
    ├── scrape.yml           # Scheduled scrape action
    └── deploy-pages.yml     # Deploy to GitHub Pages
```

**Structure Decision**: Hybrid Python backend + JavaScript frontend. Python package (`mom_wiki/`) contains all backend logic. Frontend is a standalone static site deployable to GitHub Pages. Corpus data lives in `corpus/` as JSON/Markdown files (no database).

## Complexity Tracking

No constitution violations requiring justification.

## GitHub Animation Features

Per user request, leverage GitHub's animation support:

- **Animated SVG**: `docs/stats.svg` - corpus health/size visualization
- **GIF**: Optionally generate GIF sprites from LBX image data
- **GitHub Actions**: `.github/workflows/` - automated scraping with stats updates
- **Contribution Snake**: Can add contribution-snake action for README visualization

## Next Steps

Run `/speckit-tasks` to generate the implementation task list.
