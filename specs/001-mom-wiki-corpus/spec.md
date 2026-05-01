# Feature Specification: Master of Magic Wiki Corpus

**Feature Branch**: `001-mom-wiki-corpus`
**Created**: 2026-04-16
**Status**: Draft
**Input**: User description: "Building a corpus for use by an AI Agent to answer questions from the user community about the game Master of Magic. Scrapers for websites, PDFs, and structured binary data files. UI for configuring sources. Browsing UI for viewing information as interconnected nodes in a 3D graph view. REST API access. MCP API wrapper for RAG by AI Agent. Hosted on GitHub, backed by Google Drive."

## Clarifications

### Session 2026-04-16

- Q: Which binary data file formats need support? → A: Original MoM LBX files (SPELLDAT, UNITDATA, ITEMDATA, etc.)
- Q: How is admin access protected? → A: No authentication (local-only access assumed)
- Q: What are the roles of GitHub vs Google Drive? → A: GitHub for text content; Google Drive for large binary files

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure and Scrape Data Sources (Priority: P1)

An administrator configures data sources (websites, PDF files, binary game data files) through a configuration interface. The system scrapes these sources and ingests the content into a unified knowledge base, extracting text and metadata while maintaining source attribution.

**Why this priority**: Without data ingestion, there is no corpus. This is the foundational capability that all other features depend on.

**Independent Test**: Can be fully tested by configuring a sample website URL, PDF file, and binary data file, running the scraper, and verifying the extracted content appears in storage with correct source attribution.

**Acceptance Scenarios**:

1. **Given** a website URL is configured as a source, **When** the scraper runs, **Then** the page content is extracted and stored with the source URL and timestamp.
2. **Given** a PDF file path is configured, **When** the scraper runs, **Then** the text content is extracted and stored with the file path and extraction date.
3. **Given** a binary game data file is configured, **When** the scraper runs, **Then** the structured data is parsed and stored as human-readable content with field metadata.
4. **Given** a source was previously scraped, **When** the scraper runs again, **Then** the existing record is updated (not duplicated).

---

### User Story 2 - Access Corpus via REST API (Priority: P2)

A developer or external system queries the knowledge corpus through a REST API to search for information, retrieve documents, and explore relationships between content nodes.

**Why this priority**: The REST API enables programmatic access, which is required for the MCP wrapper and any external integrations. This unlocks the corpus for consumption.

**Independent Test**: Can be tested by making API calls to search for Master of Magic content (e.g., "Arcane spell list") and verifying results contain relevant scraped content with source attribution.

**Acceptance Scenarios**:

1. **Given** the corpus contains scraped content, **When** a search query is submitted via the API, **Then** matching documents are returned ranked by relevance.
2. **Given** a document ID, **When** requested via the API, **Then** the full document content, metadata, and source information are returned.
3. **Given** a node ID, **When** relationships are requested via the API, **Then** connected nodes and relationship types are returned.

---

### User Story 3 - AI Agent Queries via MCP API (Priority: P3)

An AI Agent uses the MCP (Model Context Protocol) API to perform retrieval-augmented generation (RAG), querying the corpus for relevant Master of Magic information to answer user community questions.

**Why this priority**: This is the primary use case stated by the user. It depends on the REST API (P2) being available first.

**Independent Test**: Can be tested by connecting an AI agent to the MCP endpoint, asking "What spells does a Life wizard start with?", and verifying the agent receives relevant corpus content for its response.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** an AI agent connects, **Then** the available tools and resources are listed correctly.
2. **Given** an AI agent submits a RAG query, **When** processed, **Then** relevant corpus chunks are returned with source citations.
3. **Given** a query about Master of Magic game mechanics, **When** the MCP tool is invoked, **Then** the response includes content from multiple source types (web, PDF, binary) if available.

---

### User Story 4 - Browse Corpus in 3D Graph View (Priority: P4)

A community member explores the Master of Magic knowledge base through an interactive 3D graph visualization, where information nodes are displayed as connected entities that can be navigated, zoomed, and filtered.

**Why this priority**: Provides visual exploration for human users. Lower priority than API access since the primary use case is AI agent consumption.

**Independent Test**: Can be tested by loading the graph view, verifying nodes appear for scraped content, clicking a node to see its details, and following relationship links to connected nodes.

**Acceptance Scenarios**:

1. **Given** the corpus contains interconnected content, **When** the 3D graph view loads, **Then** nodes representing content hunks are displayed with visible connections.
2. **Given** a node is selected in the graph, **When** clicked, **Then** a detail panel shows the content, source, and related nodes.
3. **Given** the graph is displayed, **When** the user zooms or rotates, **Then** the view updates smoothly.
4. **Given** a search term is entered, **When** submitted, **Then** matching nodes are highlighted in the graph.

---

### User Story 5 - Manage Sources via Configuration UI (Priority: P5)

An administrator uses a web-based interface to add, edit, remove, and monitor data sources. They can view scraping status, trigger manual scrapes, and configure scraping schedules.

**Why this priority**: Improves administrator experience but sources can be configured via files initially. UI is a convenience layer.

**Independent Test**: Can be tested by opening the configuration UI, adding a new website source, saving it, and verifying it appears in the source list ready for scraping.

**Acceptance Scenarios**:

1. **Given** the configuration UI is open, **When** a new source is added with URL and type, **Then** it appears in the sources list.
2. **Given** a configured source, **When** the administrator clicks "Scrape Now", **Then** the scraping process starts and status updates are shown.
3. **Given** a source with errors, **When** viewing its status, **Then** error details and last successful scrape date are displayed.

---

### Edge Cases

- What happens when a website returns a 404 or is unreachable? System logs the error, marks source as failed, and continues with other sources.
- What happens when a PDF is password-protected? System skips the file, logs a warning, and reports it in source status.
- What happens when a binary file format is unrecognized? System stores raw metadata and flags for manual review.
- What happens when Google Drive sync fails? System continues operating from local cache and retries sync with exponential backoff.
- What happens when duplicate content is detected from different sources? System merges records with multiple source attributions.

## Requirements *(mandatory)*

### Functional Requirements

**Data Ingestion**
- **FR-001**: System MUST scrape content from HTTP/HTTPS websites, extracting text and preserving structure.
- **FR-002**: System MUST extract text content from PDF documents.
- **FR-003**: System MUST parse original Master of Magic LBX archive files (SPELLDAT.LBX, UNITDATA.LBX, ITEMDATA.LBX, ITEMSPOW.LBX, WIZARDS.LBX, etc.).
- **FR-004**: System MUST normalize all scraped content to a unified document schema with source URL/path, extraction timestamp, content type, and raw text.
- **FR-005**: System MUST update existing records when re-scraping (idempotent ingestion).
- **FR-006**: System MUST maintain full provenance for all content (original source, scrape date, transformation history).

**Storage & Hosting**
- **FR-007**: System MUST store extracted text content (markdown, JSON metadata) in a GitHub repository.
- **FR-008**: System MUST store large binary files (PDFs, images, LBX source files) in Google Drive with reference links in GitHub.
- **FR-009**: System MUST store extracted text in plain text or markdown format for searchability.
- **FR-010**: System MUST maintain references from GitHub-hosted documents to Google Drive-hosted binary artifacts.

**API Access**
- **FR-011**: System MUST provide a REST API for searching the corpus.
- **FR-012**: System MUST provide a REST API for retrieving individual documents by ID.
- **FR-013**: System MUST provide a REST API for exploring node relationships.
- **FR-014**: System MUST wrap the REST API as an MCP server for AI agent access.
- **FR-015**: MCP server MUST expose corpus search as a tool for RAG queries.

**User Interfaces**
- **FR-016**: System MUST provide a configuration interface for managing data sources.
- **FR-017**: System MUST provide a 3D graph visualization for browsing interconnected content nodes.
- **FR-018**: Graph view MUST support navigation (zoom, rotate, pan) and node selection.
- **FR-019**: Graph view MUST support search with visual highlighting of matching nodes.

**Content Relationships**
- **FR-020**: System MUST identify and store relationships between content nodes (e.g., spell belongs to magic school, unit has abilities).
- **FR-021**: System MUST support full-text search across all corpus content.

### Key Entities

- **Source**: A configured data origin with type (web/PDF/binary), location (URL or file path), scraping schedule, and status.
- **Document**: A piece of scraped content with unique ID, source reference, extraction timestamp, content type, raw text, and structured metadata.
- **Node**: A displayable unit of information derived from documents, with title, summary, and content for graph visualization.
- **Relationship**: A typed connection between nodes (e.g., "belongs_to", "references", "related_to") with optional weight/strength.
- **ScrapeJob**: A record of a scraping execution with start time, end time, status, and any errors encountered.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can configure a new data source and see scraped content within 5 minutes.
- **SC-002**: Full-text search returns relevant results for Master of Magic queries in under 2 seconds.
- **SC-003**: AI Agent using MCP API can answer 80% of common Master of Magic questions using corpus content.
- **SC-004**: 3D graph view loads and displays up to 1,000 nodes smoothly (no visible lag during navigation).
- **SC-005**: Re-scraping a previously ingested source updates content without creating duplicates.
- **SC-006**: Users can trace any piece of information back to its original source within 2 clicks.
- **SC-007**: System remains functional if Google Drive is temporarily unavailable (graceful degradation).

## Assumptions

- Target users are Master of Magic community members and AI agents; no authentication required for read-only access.
- Admin operations (source configuration, scraping) run locally only; no authentication needed as access is controlled by local machine access.
- Original Master of Magic (1994) LBX archive format is well-documented by the community and existing parsers are available as reference.
- GitHub repository hosts text content (extracted markdown, metadata JSON); Google Drive hosts large binary files (PDFs, images, original LBX files) to respect GitHub size limits.
- Initial scope focuses on English-language content only.
- The 3D graph view is web-based and runs in modern browsers (Chrome, Firefox, Edge, Safari).
- MCP API follows the standard Model Context Protocol specification for tool/resource definitions.
- Scraping respects robots.txt and rate limits for external websites.
