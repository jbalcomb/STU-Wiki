"""MCP Server implementation for Master of Magic Wiki Corpus."""

import asyncio
import json
import logging
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    ResourceContents,
    TextResourceContents,
)

from ..storage import CorpusStorage
from ..search import SearchIndex

logger = logging.getLogger(__name__)

# Shared storage and search index
_storage: Optional[CorpusStorage] = None
_search_index: Optional[SearchIndex] = None


def get_storage() -> CorpusStorage:
    global _storage
    if _storage is None:
        _storage = CorpusStorage()
    return _storage


def get_search_index() -> SearchIndex:
    global _search_index
    if _search_index is None:
        _search_index = SearchIndex(get_storage())
    return _search_index


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("mom-wiki-corpus")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="search_corpus",
                description="Search the Master of Magic Wiki corpus for information. Use for general queries about spells, units, items, wizards, or game mechanics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10
                        },
                        "type": {
                            "type": "string",
                            "description": "Filter by type: 'document' or 'node'",
                            "enum": ["document", "node"]
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_document",
                description="Get the full content of a specific document by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "Document ID"
                        }
                    },
                    "required": ["document_id"]
                }
            ),
            Tool(
                name="get_related",
                description="Get nodes related to a specific node by ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "node_id": {
                            "type": "string",
                            "description": "Node ID"
                        },
                        "relationship_type": {
                            "type": "string",
                            "description": "Filter by relationship type",
                            "enum": ["requires", "synergy", "counter", "summons", "grants", "belongs_to", "related"]
                        }
                    },
                    "required": ["node_id"]
                }
            ),
            Tool(
                name="list_spells",
                description="List spells, optionally filtered by realm or rarity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "realm": {
                            "type": "string",
                            "description": "Filter by magic realm",
                            "enum": ["Life", "Death", "Nature", "Sorcery", "Chaos", "Arcane"]
                        },
                        "rarity": {
                            "type": "string",
                            "description": "Filter by rarity",
                            "enum": ["Common", "Uncommon", "Rare", "Very Rare"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results",
                            "default": 20
                        }
                    }
                }
            ),
            Tool(
                name="list_units",
                description="List units, optionally filtered by race or type.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "race": {
                            "type": "string",
                            "description": "Filter by race (e.g., 'High Elf', 'Orc')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results",
                            "default": 20
                        }
                    }
                }
            ),
            Tool(
                name="get_game_mechanic",
                description="Get detailed information about a specific game mechanic or concept.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The game mechanic or concept to look up (e.g., 'combat', 'magic resistance', 'city building')"
                        }
                    },
                    "required": ["topic"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "search_corpus":
                return await handle_search_corpus(arguments)
            elif name == "get_document":
                return await handle_get_document(arguments)
            elif name == "get_related":
                return await handle_get_related(arguments)
            elif name == "list_spells":
                return await handle_list_spells(arguments)
            elif name == "list_units":
                return await handle_list_units(arguments)
            elif name == "get_game_mechanic":
                return await handle_get_game_mechanic(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]
        except Exception as e:
            logger.error(f"Error in tool {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="corpus://stats",
                name="Corpus Statistics",
                description="Current statistics about the MoM Wiki corpus",
                mimeType="application/json"
            ),
            Resource(
                uri="corpus://spells",
                name="All Spells",
                description="List of all spells in the corpus",
                mimeType="application/json"
            ),
            Resource(
                uri="corpus://units",
                name="All Units",
                description="List of all units in the corpus",
                mimeType="application/json"
            )
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> ResourceContents:
        """Read a resource by URI."""
        storage = get_storage()

        if uri == "corpus://stats":
            stats = storage.update_stats()
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps(stats, indent=2)
            )

        elif uri == "corpus://spells":
            spells = storage.list_nodes(node_type="spell")
            data = [
                {
                    "id": s.id,
                    "name": s.name,
                    "realm": s.attributes.realm.value if s.attributes.realm else None,
                    "rarity": s.attributes.rarity.value if s.attributes.rarity else None,
                    "cost": s.attributes.cost,
                    "summary": s.summary
                }
                for s in spells
            ]
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps(data, indent=2)
            )

        elif uri == "corpus://units":
            units = storage.list_nodes(node_type="unit")
            data = [
                {
                    "id": u.id,
                    "name": u.name,
                    "race": u.attributes.stats.get("race"),
                    "attack": u.attributes.stats.get("attack"),
                    "defense": u.attributes.stats.get("defense"),
                    "summary": u.summary
                }
                for u in units
            ]
            return TextResourceContents(
                uri=uri,
                mimeType="application/json",
                text=json.dumps(data, indent=2)
            )

        elif uri.startswith("corpus://document/"):
            doc_id = uri.replace("corpus://document/", "")
            doc = storage.get_document(doc_id)
            if not doc:
                return TextResourceContents(
                    uri=uri,
                    mimeType="text/plain",
                    text=f"Document not found: {doc_id}"
                )
            content = storage.get_document_content(doc_id) or ""
            return TextResourceContents(
                uri=uri,
                mimeType="text/markdown",
                text=content
            )

        return TextResourceContents(
            uri=uri,
            mimeType="text/plain",
            text=f"Unknown resource: {uri}"
        )

    return server


async def handle_search_corpus(args: dict) -> list[TextContent]:
    """Handle search_corpus tool."""
    query = args.get("query", "")
    limit = args.get("limit", 10)
    item_type = args.get("type")

    index = get_search_index()
    results = index.search(query, limit=limit, item_type=item_type)

    if not results:
        return [TextContent(type="text", text=f"No results found for: {query}")]

    output = f"Found {len(results)} results for '{query}':\n\n"
    for r in results:
        output += f"### {r.title}\n"
        output += f"- Type: {r.type}\n"
        output += f"- Score: {r.score:.1f}\n"
        output += f"- Summary: {r.summary[:200]}...\n"
        if r.highlights:
            output += f"- Highlights: {r.highlights[0]}\n"
        output += "\n"

    return [TextContent(type="text", text=output)]


async def handle_get_document(args: dict) -> list[TextContent]:
    """Handle get_document tool."""
    doc_id = args.get("document_id", "")
    storage = get_storage()

    doc = storage.get_document(doc_id)
    if not doc:
        return [TextContent(type="text", text=f"Document not found: {doc_id}")]

    content = storage.get_document_content(doc_id) or "No content available"

    output = f"# {doc.title}\n\n"
    output += f"**Source ID**: {doc.source_id}\n"
    if doc.url:
        output += f"**URL**: {doc.url}\n"
    if doc.file_path:
        output += f"**File**: {doc.file_path}\n"
    output += f"\n---\n\n{content}"

    return [TextContent(type="text", text=output)]


async def handle_get_related(args: dict) -> list[TextContent]:
    """Handle get_related tool."""
    node_id = args.get("node_id", "")
    rel_type_str = args.get("relationship_type")

    storage = get_storage()

    node = storage.get_node(node_id)
    if not node:
        return [TextContent(type="text", text=f"Node not found: {node_id}")]

    from ..models import RelationshipType
    rel_type = None
    if rel_type_str:
        try:
            rel_type = RelationshipType(rel_type_str)
        except ValueError:
            pass

    related = storage.get_related_nodes(node_id, rel_type=rel_type)

    if not related:
        return [TextContent(type="text", text=f"No related nodes found for: {node.name}")]

    output = f"# Related to: {node.name}\n\n"
    for r in related:
        rel_node = r["node"]
        rel = r["relationship"]
        direction = r["direction"]
        output += f"- **{rel_node.name}** ({rel_node.type.value})\n"
        output += f"  - Relationship: {rel.type.value} ({direction})\n"
        output += f"  - {rel_node.summary[:100]}...\n\n"

    return [TextContent(type="text", text=output)]


async def handle_list_spells(args: dict) -> list[TextContent]:
    """Handle list_spells tool."""
    realm = args.get("realm")
    rarity = args.get("rarity")
    limit = args.get("limit", 20)

    storage = get_storage()
    spells = storage.list_nodes(node_type="spell", realm=realm)

    # Filter by rarity if specified
    if rarity:
        spells = [s for s in spells if s.attributes.rarity and s.attributes.rarity.value == rarity]

    spells = spells[:limit]

    if not spells:
        return [TextContent(type="text", text="No spells found with the specified filters.")]

    output = f"# Spells ({len(spells)} found)\n\n"
    for spell in spells:
        output += f"## {spell.name}\n"
        if spell.attributes.realm:
            output += f"- Realm: {spell.attributes.realm.value}\n"
        if spell.attributes.rarity:
            output += f"- Rarity: {spell.attributes.rarity.value}\n"
        if spell.attributes.cost:
            output += f"- Cost: {spell.attributes.cost}\n"
        output += f"- {spell.summary}\n\n"

    return [TextContent(type="text", text=output)]


async def handle_list_units(args: dict) -> list[TextContent]:
    """Handle list_units tool."""
    race = args.get("race")
    limit = args.get("limit", 20)

    storage = get_storage()
    units = storage.list_nodes(node_type="unit")

    # Filter by race if specified
    if race:
        units = [u for u in units if u.attributes.stats.get("race") == race]

    units = units[:limit]

    if not units:
        return [TextContent(type="text", text="No units found with the specified filters.")]

    output = f"# Units ({len(units)} found)\n\n"
    for unit in units:
        stats = unit.attributes.stats
        output += f"## {unit.name}\n"
        if stats.get("race"):
            output += f"- Race: {stats['race']}\n"
        if stats.get("attack"):
            output += f"- Attack: {stats['attack']}\n"
        if stats.get("defense"):
            output += f"- Defense: {stats['defense']}\n"
        output += f"- {unit.summary}\n\n"

    return [TextContent(type="text", text=output)]


async def handle_get_game_mechanic(args: dict) -> list[TextContent]:
    """Handle get_game_mechanic tool."""
    topic = args.get("topic", "")

    index = get_search_index()
    # Search for concepts and pages related to the topic
    results = index.search(
        topic,
        limit=5,
        item_type="node"
    )

    if not results:
        return [TextContent(type="text", text=f"No information found about: {topic}")]

    storage = get_storage()
    output = f"# Game Mechanic: {topic}\n\n"

    for r in results:
        node = storage.get_node(r.id)
        if node:
            output += f"## {node.name}\n\n"
            output += f"{node.content}\n\n"
            output += "---\n\n"

    return [TextContent(type="text", text=output)]


async def serve():
    """Run the MCP server."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point for MCP server."""
    asyncio.run(serve())


if __name__ == "__main__":
    main()
