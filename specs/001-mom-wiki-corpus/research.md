# Research: Master of Magic Wiki Corpus

**Branch**: `001-mom-wiki-corpus` | **Date**: 2026-04-16

## Technology Decisions

### Python Stack (Local Scrapers & API)

**Decision**: Python 3.11+ with standard library + minimal dependencies

**Rationale**:
- User specified Python for local tooling
- Rich ecosystem for web scraping (requests, BeautifulSoup), PDF extraction (PyMuPDF/pdfplumber), and binary parsing (struct)
- FastAPI or Flask for REST API (lightweight, easy MCP integration)
- No database required - JSON/Markdown files serve as storage

**Alternatives considered**:
- Node.js: Good for web, but Python has better binary parsing and PDF libraries
- Go: Fast but smaller ecosystem for document processing

### JavaScript Stack (Website)

**Decision**: Vanilla JavaScript or lightweight framework for static GitHub Pages site

**Rationale**:
- User specified JavaScript for website
- 3D graph visualization via Three.js or Force-Graph
- GitHub Pages hosting (static files only)
- No build step required for simple deployment

**Alternatives considered**:
- React/Vue: Overkill for a visualization-focused wiki browser
- WebGL raw: Three.js provides better abstraction

### Storage: Text Files (No Database)

**Decision**: JSON files for structured data, Markdown for content

**Rationale**:
- User explicitly stated "no databases - data is text files"
- Git-friendly (diff, merge, version control)
- Human-readable and editable
- GitHub renders Markdown natively

**File structure**:
- `corpus/documents/*.json` - scraped document metadata
- `corpus/content/*.md` - extracted text content
- `corpus/nodes/*.json` - graph node definitions
- `corpus/relationships.json` - node connections
- `sources.json` - configured data sources

### GitHub Animation Support

**Decision**: Leverage GitHub's native animation rendering

**Rationale**:
- User wants to use GitHub's animation capabilities
- Supported formats: GIF, SVG (animated), MP4/MOV (≤10MB)
- GitHub Actions can generate dynamic content (contribution snake pattern)

**Use cases**:
- Animated SVG diagrams showing spell effects or unit stats
- GIF walkthroughs of game mechanics
- GitHub Actions workflow to generate corpus statistics visualization
- Dynamic SVG badges showing corpus health/size

### LBX Parser

**Decision**: Custom Python LBX parser based on community documentation

**Rationale**:
- Original MoM (1994) LBX format is well-documented
- Existing open-source parsers available as reference (e.g., OpenMOM, CivOne)
- Key files: SPELLDAT.LBX, UNITDATA.LBX, ITEMDATA.LBX, WIZARDS.LBX

**Data structures to extract**:
- Spells: name, realm, cost, effects, research cost
- Units: name, stats (attack, defense, movement), abilities, upkeep
- Items: name, powers, crafting cost
- Wizards: name, portrait, starting spells, traits

### MCP Server Implementation

**Decision**: Python MCP server wrapping the REST API

**Rationale**:
- MCP SDK available for Python
- Exposes corpus search as tools for AI agents
- Resources expose document collections
- Thin wrapper over existing REST endpoints

**Tools to expose**:
- `search_corpus`: Full-text search with filters
- `get_document`: Retrieve specific document by ID
- `get_related`: Get nodes related to a given node
- `list_spells`, `list_units`, etc.: Domain-specific queries

### 3D Graph Visualization

**Decision**: Force-Graph 3D (based on Three.js)

**Rationale**:
- Purpose-built for 3D node-link graphs
- Handles 1000+ nodes smoothly (per SC-004)
- Interactive: zoom, rotate, pan, click
- Works with static JSON data

**Alternatives considered**:
- D3.js: 2D-focused, 3D requires more work
- Sigma.js: Good for large graphs but 2D
- Custom Three.js: More control but more development effort

### Google Drive Integration

**Decision**: Google Drive API for large file storage with reference links

**Rationale**:
- PDFs, images, original LBX files stored in Drive (exceeds GitHub 100MB limit)
- GitHub stores extracted text + Drive links
- Drive API via Python for upload/download
- Public sharing links for read access

**Sync strategy**:
- On scrape: upload binary to Drive, store link in JSON
- Local cache for offline operation
- Exponential backoff on sync failures

## Best Practices Research

### Web Scraping

- Respect robots.txt
- Rate limiting (1 request/second default)
- User-Agent identification
- Handle redirects, 404s gracefully
- Store raw HTML alongside extracted text for re-processing

### PDF Extraction

- PyMuPDF (fitz) for text extraction
- Handle scanned PDFs (OCR fallback with Tesseract if needed)
- Preserve document structure (headings, lists)
- Extract images with references

### Full-Text Search (No Database)

**Decision**: In-memory search index built from JSON files

**Options**:
- Lunr.js for browser-side search
- Whoosh (Python) for server-side
- Simple JSON scan for small corpus (<10k documents)

**Hybrid approach**:
- Pre-build search index as JSON during scrape
- Load index in browser for instant search
- Server-side fallback for complex queries

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Binary format support | Original MoM LBX files only (per clarification) |
| Admin authentication | Local-only access, no auth needed (per clarification) |
| GitHub vs Drive roles | GitHub for text, Drive for binaries (per clarification) |
| Python vs Node | Python for backend (user specified) |
| Database | None - text files only (user specified) |
