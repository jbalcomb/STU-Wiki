# Tasks: Master of Magic Wiki Corpus

**Input**: Design documents from `specs/001-mom-wiki-corpus/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/, research.md, quickstart.md

**Tests**: Tests are OPTIONAL - not explicitly requested in specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create Python package structure in mom_wiki/__init__.py
- [x] T002 [P] Create requirements.txt with dependencies (FastAPI, requests, BeautifulSoup4, PyMuPDF, google-api-python-client, mcp)
- [x] T003 [P] Create frontend package.json with dependencies (three, 3d-force-graph, lunr)
- [x] T004 [P] Create config/settings.json with default configuration
- [x] T005 [P] Create .gitignore with Python, Node, and credentials exclusions
- [x] T006 [P] Create corpus/ directory structure (documents/, content/, nodes/, jobs/)
- [x] T007 [P] Create data/ directory structure (lbx/, pdf/)
- [x] T008 [P] Create empty sources.json with schema example

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Create Source model (Pydantic) in mom_wiki/models/source.py
- [x] T010 [P] Create Document model (Pydantic) in mom_wiki/models/document.py
- [x] T011 [P] Create Node model (Pydantic) in mom_wiki/models/node.py
- [x] T012 [P] Create Relationship model (Pydantic) in mom_wiki/models/relationship.py
- [x] T013 [P] Create ScrapeJob model (Pydantic) in mom_wiki/models/scrape_job.py
- [x] T014 Create models __init__.py exporting all models in mom_wiki/models/__init__.py
- [x] T015 Create corpus storage module with JSON file read/write in mom_wiki/storage/corpus.py
- [x] T016 [P] Create Google Drive storage module with upload/download in mom_wiki/storage/drive.py
- [x] T017 Create storage __init__.py in mom_wiki/storage/__init__.py
- [x] T018 Create abstract base scraper class in mom_wiki/scrapers/base.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Configure and Scrape Data Sources (Priority: P1)

**Goal**: Admin configures sources and scrapes content from web, PDF, and LBX files into unified corpus

**Independent Test**: Configure sample website URL, PDF file, and LBX file; run scraper; verify extracted content appears in corpus/ with source attribution

### Implementation for User Story 1

- [x] T019 [US1] Implement web scraper with BeautifulSoup in mom_wiki/scrapers/web_scraper.py
- [x] T020 [P] [US1] Implement PDF scraper with PyMuPDF in mom_wiki/scrapers/pdf_scraper.py
- [x] T021 [P] [US1] Implement LBX parser for SPELLDAT.LBX in mom_wiki/scrapers/lbx_scraper.py
- [x] T022 [US1] Add UNITDATA.LBX parsing to mom_wiki/scrapers/lbx_scraper.py
- [x] T023 [US1] Add ITEMDATA.LBX and WIZARDS.LBX parsing to mom_wiki/scrapers/lbx_scraper.py
- [x] T024 [US1] Create scrapers __init__.py with factory function in mom_wiki/scrapers/__init__.py
- [x] T025 [US1] Implement source configuration loader in mom_wiki/storage/corpus.py (load_sources, save_sources)
- [x] T026 [US1] Implement document storage with checksum dedup in mom_wiki/storage/corpus.py (save_document, get_document)
- [x] T027 [US1] Implement node creation from scraped content in mom_wiki/storage/corpus.py (create_node, update_node)
- [x] T028 [US1] Implement relationship storage in mom_wiki/storage/corpus.py (add_relationship)
- [x] T029 [US1] Implement scrape job tracking in mom_wiki/storage/corpus.py (create_job, update_job)
- [x] T030 [US1] Create CLI entry point with scrape command in mom_wiki/cli.py
- [x] T031 [US1] Add add-source CLI command in mom_wiki/cli.py
- [x] T032 [US1] Add status CLI command to show scrape status in mom_wiki/cli.py
- [x] T033 [US1] Implement Google Drive upload for binary sources in mom_wiki/storage/drive.py (upload_file, get_share_link)
- [x] T034 [US1] Add idempotent re-scrape logic (checksum comparison) in mom_wiki/scrapers/base.py

**Checkpoint**: User Story 1 complete - can scrape web, PDF, LBX sources and store in corpus

---

## Phase 4: User Story 2 - Access Corpus via REST API (Priority: P2)

**Goal**: Developers query corpus via REST API for search, documents, nodes, and relationships

**Independent Test**: Start API server; call GET /search?q=fireball; verify results with source attribution

### Implementation for User Story 2

- [x] T035 [US2] Create search index builder in mom_wiki/search/indexer.py
- [x] T036 [US2] Implement search function with ranking in mom_wiki/search/indexer.py
- [x] T037 [US2] Create search __init__.py in mom_wiki/search/__init__.py
- [x] T038 [US2] Create FastAPI app in mom_wiki/api/main.py
- [x] T039 [US2] Implement GET /search endpoint in mom_wiki/api/routes/search.py
- [x] T040 [P] [US2] Implement GET /documents and GET /documents/{id} in mom_wiki/api/routes/documents.py
- [x] T041 [P] [US2] Implement GET /nodes and GET /nodes/{id} in mom_wiki/api/routes/nodes.py
- [x] T042 [US2] Implement GET /nodes/{id}/related in mom_wiki/api/routes/nodes.py
- [x] T043 [US2] Implement GET /graph endpoint in mom_wiki/api/routes/nodes.py
- [x] T044 [P] [US2] Implement GET /sources and POST /sources in mom_wiki/api/routes/sources.py
- [x] T045 [US2] Implement POST /sources/{id}/scrape in mom_wiki/api/routes/sources.py
- [x] T046 [US2] Implement GET /jobs/{id} in mom_wiki/api/routes/sources.py
- [x] T047 [US2] Create api routes __init__.py with router registration in mom_wiki/api/routes/__init__.py
- [x] T048 [US2] Add rebuild-index CLI command in mom_wiki/cli.py

**Checkpoint**: User Story 2 complete - REST API fully functional

---

## Phase 5: User Story 3 - AI Agent Queries via MCP API (Priority: P3)

**Goal**: AI agents connect via MCP and use RAG tools to query corpus

**Independent Test**: Start MCP server; connect Claude Desktop; ask "What spells does a Life wizard start with?"; verify relevant corpus chunks returned

### Implementation for User Story 3

- [x] T049 [US3] Create MCP server entry point in mom_wiki/mcp_server/__init__.py
- [x] T050 [US3] Implement search_corpus tool in mom_wiki/mcp_server/server.py
- [x] T051 [US3] Implement get_document tool in mom_wiki/mcp_server/server.py
- [x] T052 [US3] Implement get_related tool in mom_wiki/mcp_server/server.py
- [x] T053 [P] [US3] Implement list_spells tool in mom_wiki/mcp_server/server.py
- [x] T054 [P] [US3] Implement list_units tool in mom_wiki/mcp_server/server.py
- [x] T055 [US3] Implement get_game_mechanic tool in mom_wiki/mcp_server/server.py
- [x] T056 [US3] Implement corpus://stats resource in mom_wiki/mcp_server/server.py
- [x] T057 [US3] Implement corpus://spells and corpus://units resources in mom_wiki/mcp_server/server.py
- [x] T058 [US3] Implement corpus://document/{id} resource in mom_wiki/mcp_server/server.py
- [x] T059 [US3] Add MCP server run command in mom_wiki/cli.py

**Checkpoint**: User Story 3 complete - AI agents can query via MCP

---

## Phase 6: User Story 4 - Browse Corpus in 3D Graph View (Priority: P4)

**Goal**: Community members explore corpus via interactive 3D graph visualization

**Independent Test**: Open frontend in browser; verify nodes appear; click node to see details; zoom/rotate works smoothly

### Implementation for User Story 4

- [x] T060 [US4] Create frontend HTML structure in frontend/src/index.html
- [x] T061 [US4] Create main.js entry point in frontend/src/main.js
- [x] T062 [US4] Implement 3D graph visualization with Force-Graph in frontend/src/graph.js
- [x] T063 [US4] Implement node click handler showing detail panel in frontend/src/graph.js
- [x] T064 [US4] Implement zoom/rotate/pan controls in frontend/src/graph.js
- [x] T065 [US4] Create client-side search with Lunr.js in frontend/src/search.js
- [x] T066 [US4] Implement search highlighting in graph in frontend/src/graph.js
- [x] T067 [US4] Create REST API client module in frontend/src/api.js
- [x] T068 [US4] Add node type color coding by realm/type in frontend/src/graph.js
- [x] T069 [US4] Create CSS styles in frontend/src/styles.css
- [x] T070 [US4] Create build script for GitHub Pages in frontend/package.json (build command)

**Checkpoint**: User Story 4 complete - 3D graph view functional

---

## Phase 7: User Story 5 - Manage Sources via Configuration UI (Priority: P5)

**Goal**: Admin manages sources via web UI (add, edit, remove, monitor, trigger scrapes)

**Independent Test**: Open admin UI; add new source; click "Scrape Now"; verify status updates shown

### Implementation for User Story 5

- [x] T071 [US5] Create admin panel HTML in frontend/src/admin.html
- [x] T072 [US5] Create admin.js for source management in frontend/src/admin.js
- [x] T073 [US5] Implement source list display in frontend/src/admin.js
- [x] T074 [US5] Implement add source form in frontend/src/admin.js
- [x] T075 [US5] Implement edit/delete source actions in frontend/src/admin.js
- [x] T076 [US5] Implement "Scrape Now" button with status polling in frontend/src/admin.js
- [x] T077 [US5] Display scrape job status and errors in frontend/src/admin.js
- [x] T078 [US5] Add admin styles in frontend/src/admin.css

**Checkpoint**: User Story 5 complete - Admin UI functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: GitHub integration, animations, deployment, and documentation

- [x] T079 [P] Create GitHub Actions workflow for scheduled scraping in .github/workflows/scrape.yml
- [x] T080 [P] Create GitHub Actions workflow for GitHub Pages deploy in .github/workflows/deploy-pages.yml
- [x] T081 [P] Generate animated SVG stats badge in docs/stats.svg (via Python script)
- [x] T082 Add generate-stats CLI command in mom_wiki/cli.py
- [x] T083 [P] Create docs/index.html landing page
- [x] T084 Create build-pages.sh script for deployment in scripts/build-pages.sh
- [x] T085 [P] Add sync-drive CLI command for manual Drive sync in mom_wiki/cli.py
- [x] T086 Update CLAUDE.md with final project documentation
- [x] T087 Create README.md with project overview and quickstart

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1): Can start after Phase 2
  - US2 (P2): Depends on US1 (needs corpus data to search)
  - US3 (P3): Depends on US2 (MCP wraps REST API)
  - US4 (P4): Depends on US2 (frontend calls REST API)
  - US5 (P5): Depends on US2 (admin UI calls REST API)
- **Polish (Phase 8)**: Depends on US1 minimum (needs corpus for stats)

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - MVP standalone
- **User Story 2 (P2)**: Requires US1 corpus data to be useful
- **User Story 3 (P3)**: Requires US2 REST API to wrap
- **User Story 4 (P4)**: Requires US2 REST API for data
- **User Story 5 (P5)**: Requires US2 REST API for admin operations

### Within Each User Story

- Models before storage operations
- Storage operations before scrapers (US1) / API routes (US2-5)
- Core functionality before CLI/UI integration
- Parallel [P] tasks can run concurrently

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002, T003, T004, T005, T006, T007, T008 can all run in parallel

**Phase 2 (Foundational)**:
- T010, T011, T012, T013 (models) can run in parallel after T009
- T015, T016 (storage modules) can run in parallel

**Phase 3 (US1)**:
- T019, T020, T021 (scrapers) can run in parallel after T018
- T033 (Drive) can run parallel with scraper tasks

**Phase 4 (US2)**:
- T040, T041, T044 (routes) can run in parallel after T038

**Phase 5 (US3)**:
- T053, T054 (MCP tools) can run in parallel

**Phase 8 (Polish)**:
- T079, T080, T081, T083 can all run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (scraping)
4. **STOP and VALIDATE**: Test with sample sources
5. Corpus is populated - foundation for all other stories

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test scraping → **MVP: Corpus exists**
3. Add User Story 2 → Test API → Search works
4. Add User Story 3 → Test MCP → AI agents can query
5. Add User Story 4 → Test graph → Visualization works
6. Add User Story 5 → Test admin → Full feature complete
7. Add Polish → Deploy → Production ready

### Task Counts

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Setup | 8 | 7 |
| Foundational | 10 | 6 |
| US1 (P1) | 16 | 3 |
| US2 (P2) | 14 | 4 |
| US3 (P3) | 11 | 2 |
| US4 (P4) | 11 | 0 |
| US5 (P5) | 8 | 0 |
| Polish | 9 | 5 |
| **Total** | **87** | **27** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP scope: Complete through Phase 3 (US1) for functional corpus
