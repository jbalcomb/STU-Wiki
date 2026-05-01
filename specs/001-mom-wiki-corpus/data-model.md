# Data Model: Master of Magic Wiki Corpus

**Branch**: `001-mom-wiki-corpus` | **Date**: 2026-04-16

## Overview

All data stored as JSON and Markdown files in the repository. No database required.

## Entities

### Source

Configured data origin for scraping.

**File**: `sources.json` (array of Source objects)

```json
{
  "id": "string (UUID)",
  "type": "web | pdf | lbx",
  "name": "string (display name)",
  "location": "string (URL or file path)",
  "drive_id": "string | null (Google Drive file ID for binaries)",
  "schedule": "string | null (cron expression for auto-scrape)",
  "enabled": "boolean",
  "last_scraped": "ISO8601 timestamp | null",
  "last_status": "success | failed | pending",
  "last_error": "string | null",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**Validation**:
- `id`: Required, unique
- `type`: Required, one of enum values
- `location`: Required, valid URL for web type, file path for pdf/lbx
- `drive_id`: Required for pdf/lbx types (stored in Google Drive)

---

### Document

A piece of scraped content.

**File**: `corpus/documents/{id}.json`

```json
{
  "id": "string (UUID)",
  "source_id": "string (reference to Source.id)",
  "title": "string",
  "content_path": "string (relative path to .md file)",
  "content_type": "text/markdown",
  "url": "string | null (original URL for web sources)",
  "file_path": "string | null (original file path for local sources)",
  "drive_url": "string | null (Google Drive link for binary source)",
  "extracted_at": "ISO8601 timestamp",
  "checksum": "string (SHA256 of source content for dedup)",
  "metadata": {
    "author": "string | null",
    "publish_date": "string | null",
    "tags": ["string"],
    "custom": {}
  },
  "node_ids": ["string (references to Node.id)"]
}
```

**Content file**: `corpus/content/{id}.md`
- Extracted text in Markdown format
- Headings preserved from source structure
- Images referenced via Drive links

**Validation**:
- `id`: Required, unique
- `source_id`: Required, must reference existing Source
- `checksum`: Used for idempotent updates (same checksum = no update)

---

### Node

A displayable unit of information for graph visualization.

**File**: `corpus/nodes/{id}.json`

```json
{
  "id": "string (UUID)",
  "type": "spell | unit | item | wizard | ability | realm | concept | page",
  "name": "string",
  "summary": "string (1-2 sentences)",
  "content": "string (full description, may be markdown)",
  "document_ids": ["string (references to Document.id)"],
  "attributes": {
    "realm": "string | null (Life, Death, Nature, Sorcery, Chaos, Arcane)",
    "cost": "number | null",
    "rarity": "string | null (Common, Uncommon, Rare, Very Rare)",
    "stats": {}
  },
  "image_url": "string | null (Drive link to sprite/icon)",
  "created_at": "ISO8601 timestamp",
  "updated_at": "ISO8601 timestamp"
}
```

**Node types** (extensible):
- `spell`: Magic spell with realm, cost, effects
- `unit`: Creature or hero with stats and abilities
- `item`: Magic item with powers
- `wizard`: Playable wizard with traits
- `ability`: Unit ability or spell effect
- `realm`: Magic realm (Life, Death, Nature, Sorcery, Chaos)
- `concept`: Game mechanic or rule
- `page`: Generic wiki page from web scrape

---

### Relationship

Typed connection between nodes.

**File**: `corpus/relationships.json` (array)

```json
{
  "id": "string (UUID)",
  "source_node_id": "string",
  "target_node_id": "string",
  "type": "belongs_to | has_ability | requires | counters | references | related_to",
  "weight": "number (0.0-1.0, default 1.0)",
  "metadata": {}
}
```

**Relationship types**:
- `belongs_to`: Spell belongs to realm, unit belongs to race
- `has_ability`: Unit has ability
- `requires`: Spell requires research, item requires crafting
- `counters`: Spell counters another spell
- `references`: Document references another
- `related_to`: General association

---

### ScrapeJob

Record of scraping execution.

**File**: `corpus/jobs/{id}.json`

```json
{
  "id": "string (UUID)",
  "source_id": "string",
  "started_at": "ISO8601 timestamp",
  "completed_at": "ISO8601 timestamp | null",
  "status": "running | success | failed | cancelled",
  "documents_created": "number",
  "documents_updated": "number",
  "documents_unchanged": "number",
  "errors": [
    {
      "message": "string",
      "url": "string | null",
      "timestamp": "ISO8601 timestamp"
    }
  ]
}
```

---

### SearchIndex

Pre-built search index for fast queries.

**File**: `corpus/search_index.json`

```json
{
  "version": "string",
  "built_at": "ISO8601 timestamp",
  "document_count": "number",
  "node_count": "number",
  "index": {
    "terms": {},
    "documents": {}
  }
}
```

Built by Python scraper, consumed by JavaScript frontend (Lunr.js format).

---

## File System Layout

```
corpus/
├── documents/           # Document metadata (JSON)
│   ├── {uuid}.json
│   └── ...
├── content/             # Extracted text (Markdown)
│   ├── {uuid}.md
│   └── ...
├── nodes/               # Graph nodes (JSON)
│   ├── {uuid}.json
│   └── ...
├── jobs/                # Scrape job records (JSON)
│   ├── {uuid}.json
│   └── ...
├── relationships.json   # All relationships (single file)
├── search_index.json    # Pre-built search index
└── stats.json           # Corpus statistics for visualization

sources.json             # Configured sources (root level)
```

---

## State Transitions

### Source States

```
pending → success (on successful scrape)
pending → failed (on scrape error)
success → success (on re-scrape with changes)
success → failed (on re-scrape error)
failed → success (on retry success)
failed → failed (on retry failure)
```

### ScrapeJob States

```
running → success (completed without fatal errors)
running → failed (fatal error, partial results may exist)
running → cancelled (user cancelled)
```

---

## Uniqueness & Deduplication

- **Source**: Keyed by `id`, unique `location` per `type`
- **Document**: Keyed by `id`, deduped by `checksum` (same source + same checksum = update, not create)
- **Node**: Keyed by `id`, unique `name` + `type` combination
- **Relationship**: Keyed by `id`, unique `source_node_id` + `target_node_id` + `type`

---

## Volume Estimates

Based on Master of Magic content:
- ~200 spells
- ~200 units
- ~50 items
- ~14 wizards
- ~100 abilities
- ~500 wiki pages from web sources
- **Total**: ~1,000-2,000 nodes, well within SC-004 target
