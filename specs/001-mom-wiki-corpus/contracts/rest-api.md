# REST API Contract

**Base URL**: `http://localhost:8000` (local development)

> Endpoints are mounted at the root. There is no `/api/v1` prefix today; if
> versioning is added later, this contract should be updated alongside the
> route prefix change.

## Endpoints

### Search

#### `GET /search`

Full-text search across corpus.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `type` | string | No | Filter by node type (spell, unit, item, etc.) |
| `realm` | string | No | Filter by magic realm |
| `limit` | integer | No | Max results (default: 20, max: 100) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Response** `200 OK`:
```json
{
  "query": "fireball",
  "total": 5,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": "uuid",
      "type": "spell",
      "name": "Fireball",
      "summary": "Chaos combat spell dealing fire damage",
      "score": 0.95,
      "highlights": ["<em>Fireball</em> deals 5 fire damage..."]
    }
  ]
}
```

**Response** `400 Bad Request`:
```json
{
  "error": "Missing required parameter: q"
}
```

---

### Documents

#### `GET /documents`

List all documents.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_id` | string | No | Filter by source |
| `limit` | integer | No | Max results (default: 50) |
| `offset` | integer | No | Pagination offset |

**Response** `200 OK`:
```json
{
  "total": 150,
  "documents": [
    {
      "id": "uuid",
      "title": "Spell List - Chaos",
      "source_id": "uuid",
      "extracted_at": "2026-04-16T12:00:00Z",
      "url": "https://masterofmagic.fandom.com/wiki/Chaos_Spells"
    }
  ]
}
```

#### `GET /documents/{id}`

Get document by ID.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "title": "Spell List - Chaos",
  "content": "# Chaos Spells\n\nChaos magic focuses on...",
  "source_id": "uuid",
  "url": "https://...",
  "extracted_at": "2026-04-16T12:00:00Z",
  "metadata": {
    "tags": ["spells", "chaos"]
  },
  "node_ids": ["uuid1", "uuid2"]
}
```

**Response** `404 Not Found`:
```json
{
  "error": "Document not found"
}
```

---

### Nodes

#### `GET /nodes`

List all nodes.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by node type |
| `realm` | string | No | Filter by realm |
| `limit` | integer | No | Max results (default: 100) |
| `offset` | integer | No | Pagination offset |

**Response** `200 OK`:
```json
{
  "total": 500,
  "nodes": [
    {
      "id": "uuid",
      "type": "spell",
      "name": "Fireball",
      "summary": "Chaos combat spell",
      "realm": "Chaos"
    }
  ]
}
```

#### `GET /nodes/{id}`

Get node by ID with full details.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "type": "spell",
  "name": "Fireball",
  "summary": "Chaos combat spell dealing fire damage",
  "content": "Fireball is a Chaos combat spell...",
  "attributes": {
    "realm": "Chaos",
    "cost": 10,
    "rarity": "Common"
  },
  "image_url": "https://drive.google.com/...",
  "document_ids": ["uuid1"],
  "created_at": "2026-04-16T12:00:00Z"
}
```

#### `GET /nodes/{id}/related`

Get nodes related to a given node.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by relationship type |
| `direction` | string | No | `outgoing`, `incoming`, or `both` (default) |

**Response** `200 OK`:
```json
{
  "node_id": "uuid",
  "relationships": [
    {
      "id": "rel-uuid",
      "type": "belongs_to",
      "direction": "outgoing",
      "node": {
        "id": "target-uuid",
        "type": "realm",
        "name": "Chaos"
      },
      "weight": 1.0
    }
  ]
}
```

---

### Graph

#### `GET /graph`

Get full graph data for visualization.

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `types` | string | No | Comma-separated node types to include |
| `max_nodes` | integer | No | Limit nodes (default: 1000) |

**Response** `200 OK`:
```json
{
  "nodes": [
    {
      "id": "uuid",
      "type": "spell",
      "name": "Fireball",
      "group": "Chaos"
    }
  ],
  "links": [
    {
      "source": "uuid1",
      "target": "uuid2",
      "type": "belongs_to",
      "weight": 1.0
    }
  ]
}
```

---

### Sources (Admin - Local Only)

#### `GET /sources`

List configured sources.

**Response** `200 OK`:
```json
{
  "sources": [
    {
      "id": "uuid",
      "type": "web",
      "name": "MoM Fandom Wiki",
      "location": "https://masterofmagic.fandom.com/",
      "enabled": true,
      "last_scraped": "2026-04-16T12:00:00Z",
      "last_status": "success"
    }
  ]
}
```

#### `POST /sources`

Add a new source.

**Request Body**:
```json
{
  "type": "web",
  "name": "MoM Fandom Wiki",
  "location": "https://masterofmagic.fandom.com/",
  "enabled": true
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "type": "web",
  "name": "MoM Fandom Wiki",
  ...
}
```

#### `POST /sources/{id}/scrape`

Trigger scrape for a source.

**Response** `202 Accepted`:
```json
{
  "job_id": "uuid",
  "status": "running",
  "message": "Scrape started"
}
```

#### `GET /jobs/{id}`

Get scrape job status.

**Response** `200 OK`:
```json
{
  "id": "uuid",
  "source_id": "uuid",
  "status": "running",
  "started_at": "2026-04-16T12:00:00Z",
  "documents_created": 5,
  "documents_updated": 2
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

| Status | Code | Description |
|--------|------|-------------|
| 400 | `BAD_REQUEST` | Invalid parameters |
| 404 | `NOT_FOUND` | Resource not found |
| 500 | `INTERNAL_ERROR` | Server error |

---

## Headers

**Request**:
- `Content-Type: application/json` (for POST/PUT)

**Response**:
- `Content-Type: application/json`
- `X-Request-Id: uuid` (for debugging)
