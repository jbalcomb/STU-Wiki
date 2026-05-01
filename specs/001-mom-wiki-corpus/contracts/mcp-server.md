# MCP Server Contract

**Server Name**: `mom-wiki-corpus`
**Protocol Version**: MCP 1.0

## Server Capabilities

```json
{
  "capabilities": {
    "tools": {},
    "resources": {}
  }
}
```

---

## Tools

### `search_corpus`

Search the Master of Magic knowledge corpus.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query (e.g., 'chaos spells', 'swordsmen unit')"
    },
    "type": {
      "type": "string",
      "enum": ["spell", "unit", "item", "wizard", "ability", "concept"],
      "description": "Filter by content type"
    },
    "realm": {
      "type": "string",
      "enum": ["Life", "Death", "Nature", "Sorcery", "Chaos", "Arcane"],
      "description": "Filter by magic realm"
    },
    "limit": {
      "type": "integer",
      "default": 5,
      "maximum": 20,
      "description": "Maximum results to return"
    }
  },
  "required": ["query"]
}
```

**Output**:
```json
{
  "results": [
    {
      "name": "Fireball",
      "type": "spell",
      "summary": "Chaos combat spell dealing 5 fire damage to a target unit",
      "realm": "Chaos",
      "source": "MoM Wiki: Chaos Spells"
    }
  ],
  "total": 3,
  "query": "fireball"
}
```

---

### `get_document`

Retrieve a specific document by ID or name.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Document UUID"
    },
    "name": {
      "type": "string",
      "description": "Document or node name (alternative to ID)"
    }
  }
}
```

**Output**:
```json
{
  "id": "uuid",
  "title": "Fireball",
  "content": "Fireball is a Chaos Realm combat spell...",
  "source": "https://masterofmagic.fandom.com/wiki/Fireball",
  "extracted_at": "2026-04-16T12:00:00Z"
}
```

---

### `get_related`

Get content related to a given topic.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Name of spell, unit, item, etc."
    },
    "relationship": {
      "type": "string",
      "enum": ["belongs_to", "has_ability", "requires", "counters", "related_to"],
      "description": "Type of relationship to find"
    }
  },
  "required": ["name"]
}
```

**Output**:
```json
{
  "name": "Fireball",
  "related": [
    {
      "name": "Chaos",
      "type": "realm",
      "relationship": "belongs_to"
    },
    {
      "name": "Fire Elemental",
      "type": "unit",
      "relationship": "related_to"
    }
  ]
}
```

---

### `list_spells`

List all spells with optional filters.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "realm": {
      "type": "string",
      "enum": ["Life", "Death", "Nature", "Sorcery", "Chaos", "Arcane"]
    },
    "rarity": {
      "type": "string",
      "enum": ["Common", "Uncommon", "Rare", "Very Rare"]
    },
    "combat_only": {
      "type": "boolean",
      "description": "Only combat spells"
    }
  }
}
```

**Output**:
```json
{
  "spells": [
    {
      "name": "Fireball",
      "realm": "Chaos",
      "rarity": "Common",
      "cost": 10,
      "summary": "Deals 5 fire damage"
    }
  ],
  "count": 50
}
```

---

### `list_units`

List all units with optional filters.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "race": {
      "type": "string",
      "description": "Filter by race (e.g., High Elf, Orc)"
    },
    "fantastic": {
      "type": "boolean",
      "description": "Only fantastic (summoned) creatures"
    },
    "realm": {
      "type": "string",
      "description": "For fantastic units, filter by summoning realm"
    }
  }
}
```

**Output**:
```json
{
  "units": [
    {
      "name": "High Elf Swordsmen",
      "race": "High Elf",
      "attack": 3,
      "defense": 3,
      "movement": 2,
      "abilities": ["Forester"]
    }
  ],
  "count": 150
}
```

---

### `get_game_mechanic`

Explain a game mechanic or concept.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string",
      "description": "Mechanic name (e.g., 'combat resolution', 'mana income')"
    }
  },
  "required": ["topic"]
}
```

**Output**:
```json
{
  "topic": "Combat Resolution",
  "explanation": "Combat in Master of Magic uses...",
  "related_topics": ["Attack Strength", "Defense", "To-Hit Rolls"],
  "source": "MoM Wiki: Combat"
}
```

---

## Resources

### `corpus://stats`

Corpus statistics.

**URI**: `corpus://stats`

**Content**:
```json
{
  "document_count": 500,
  "node_count": 1200,
  "spell_count": 200,
  "unit_count": 200,
  "last_updated": "2026-04-16T12:00:00Z"
}
```

---

### `corpus://spells`

List of all spells as a resource.

**URI**: `corpus://spells`
**MIME Type**: `application/json`

---

### `corpus://units`

List of all units as a resource.

**URI**: `corpus://units`
**MIME Type**: `application/json`

---

### `corpus://document/{id}`

Individual document content.

**URI Template**: `corpus://document/{id}`
**MIME Type**: `text/markdown`

---

## Usage Examples

### Example 1: Answer a question about spells

```
User: "What spells counter undead?"

AI Agent:
1. Calls search_corpus(query="counter undead", type="spell")
2. Receives results: Holy Word, Consecration, Dispel Evil
3. Calls get_document(name="Holy Word") for details
4. Formulates answer with source citations
```

### Example 2: Compare units

```
User: "How do High Elf Swordsmen compare to Orc Swordsmen?"

AI Agent:
1. Calls list_units(race="High Elf") and list_units(race="Orc")
2. Extracts swordsmen entries
3. Compares stats and abilities
4. Provides comparison with source
```

---

## Error Handling

Tools return errors in this format:

```json
{
  "error": true,
  "message": "Node not found: Firebolt",
  "suggestion": "Did you mean: Fireball?"
}
```
