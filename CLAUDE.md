# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project uses **Spec Kit** (Specify), a specification-driven development framework. Features are developed through a structured workflow: specify → plan → tasks → implement.

## Spec Kit Workflow

The development workflow follows these stages:

1. **Specify** (`speckit-specify` skill): Create feature specifications from natural language descriptions
2. **Plan** (`speckit-plan` skill): Generate implementation plans based on specifications
3. **Tasks** (`speckit-tasks` skill): Generate actionable task lists from design artifacts
4. **Implement** (`speckit-implement` skill): Execute tasks defined in tasks.md

Additional skills available:
- `speckit-clarify`: Ask clarification questions about feature specs
- `speckit-checklist`: Generate custom checklists for features
- `speckit-analyze`: Cross-artifact consistency analysis
- `speckit-constitution`: Manage project principles/constitution
- `speckit-taskstoissues`: Convert tasks to GitHub issues

## Project Structure

```
.specify/
├── memory/constitution.md    # Project principles (customize this)
├── templates/                # Templates for spec, plan, tasks
├── extensions/git/           # Git branching workflow extension
└── workflows/                # Workflow definitions

specs/                        # Feature specifications (created per-feature)
└── ###-feature-name/
    ├── spec.md              # Feature specification
    ├── plan.md              # Implementation plan
    ├── tasks.md             # Task list
    └── research.md          # Research notes
```

## Git Branching

Branch numbering is set to `sequential` (format: `001-feature-name`). The git extension handles:
- Feature branch creation before specification
- Auto-commits after Spec Kit commands (configurable in `.specify/extensions/git/git-config.yml`)

## Key Configuration

- **Integration**: Claude Code
- **Script shell**: sh (bash scripts in `.specify/scripts/bash/`)
- **Spec Kit version**: 0.7.2.dev0

## Getting Started

1. **Set up constitution**: Customize `.specify/memory/constitution.md` with project principles (use `speckit-constitution` skill)
2. **Create a feature**: Use `/speckit-specify <feature description>` to start a new feature
3. **Follow the workflow**: plan → tasks → implement

## Active Technologies
- Python 3.11+ (scrapers, API, MCP server), JavaScript ES2022+ (frontend) (001-mom-wiki-corpus)
- JSON files + Markdown files (no database) (001-mom-wiki-corpus)

## Project Components

### Python Backend (`mom_wiki/`)
- **models/**: Pydantic models (Source, Document, Node, Relationship, ScrapeJob)
- **scrapers/**: Web (BeautifulSoup), PDF (PyMuPDF), LBX (binary game data)
- **storage/**: File-based corpus storage, Google Drive integration
- **search/**: Full-text search with Lunr-style indexing
- **api/**: FastAPI REST endpoints
- **mcp_server/**: MCP protocol server for AI agents
- **cli.py**: Command-line interface

### Frontend (`frontend/src/`)
- **index.html**: 3D graph explorer (Three.js + Force-Graph-3D)
- **admin.html**: Source management panel
- **api.js**: REST API client
- **search.js**: Client-side Lunr.js search
- **graph.js**: 3D visualization

### CLI Commands
```bash
python -m mom_wiki.cli scrape         # Run scrapers
python -m mom_wiki.cli add-source     # Add a source
python -m mom_wiki.cli status         # Show corpus status
python -m mom_wiki.cli serve          # Start REST API
python -m mom_wiki.cli mcp-serve      # Start MCP server
python -m mom_wiki.cli rebuild-index  # Rebuild search index
python -m mom_wiki.cli generate-stats # Generate SVG badge
```

## Data Storage
- **corpus/documents/**: Document JSON metadata
- **corpus/content/**: Markdown content files
- **corpus/nodes/**: Node JSON files
- **corpus/jobs/**: Scrape job records
- **sources.json**: Configured data sources

## Recent Changes
- 001-mom-wiki-corpus: Full implementation complete
  - Phase 1-2: Setup and foundational models
  - Phase 3: Web, PDF, LBX scrapers with idempotent ingestion
  - Phase 4: REST API with search, documents, nodes, sources endpoints
  - Phase 5: MCP server with RAG tools
  - Phase 6: 3D graph visualization
  - Phase 7: Admin UI for source management
  - Phase 8: GitHub Actions, stats badge, documentation
