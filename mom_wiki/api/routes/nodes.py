"""Node API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ...storage import CorpusStorage
from ...models import RelationshipType

router = APIRouter(prefix="/nodes", tags=["nodes"])

_storage = CorpusStorage()


@router.get("")
async def list_nodes(
    type: Optional[str] = Query(None, description="Filter by node type (spell, unit, etc.)"),
    realm: Optional[str] = Query(None, description="Filter by magic realm"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """List all nodes with optional filtering."""
    nodes = _storage.list_nodes(node_type=type, realm=realm)

    # Pagination
    total = len(nodes)
    nodes = nodes[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "nodes": [
            {
                "id": node.id,
                "type": node.type.value,
                "name": node.name,
                "summary": node.summary,
                "realm": node.attributes.realm.value if node.attributes.realm else None,
                "rarity": node.attributes.rarity.value if node.attributes.rarity else None,
                "cost": node.attributes.cost
            }
            for node in nodes
        ]
    }


# NOTE: Static routes must come BEFORE dynamic routes like /{node_id}
@router.get("/graph")
async def get_graph(
    type: Optional[str] = Query(None, description="Filter nodes by type"),
    realm: Optional[str] = Query(None, description="Filter nodes by realm"),
    limit: int = Query(200, ge=1, le=1000, description="Maximum nodes")
):
    """
    Get graph data for visualization.

    Returns nodes and edges in a format suitable for 3D graph rendering.
    """
    nodes = _storage.list_nodes(node_type=type, realm=realm)[:limit]
    relationships = _storage.load_relationships()

    # Build node ID set for filtering edges
    node_ids = {n.id for n in nodes}

    # Filter relationships to only include visible nodes
    edges = [
        {
            "source": r.source_node_id,
            "target": r.target_node_id,
            "type": r.type.value,
            "weight": r.weight
        }
        for r in relationships
        if r.source_node_id in node_ids and r.target_node_id in node_ids
    ]

    # Color mapping for visualization
    realm_colors = {
        "Life": "#FFD700",
        "Death": "#800080",
        "Nature": "#228B22",
        "Sorcery": "#4169E1",
        "Chaos": "#FF4500",
        "Arcane": "#C0C0C0"
    }

    type_colors = {
        "spell": "#FF6B6B",
        "unit": "#4ECDC4",
        "item": "#45B7D1",
        "wizard": "#96CEB4",
        "ability": "#FFEAA7",
        "realm": "#DDA0DD",
        "concept": "#98D8C8",
        "page": "#A8E6CF"
    }

    return {
        "nodes": [
            {
                "id": node.id,
                "name": node.name,
                "type": node.type.value,
                "summary": node.summary,
                "realm": node.attributes.realm.value if node.attributes.realm else None,
                "color": (
                    realm_colors.get(node.attributes.realm.value)
                    if node.attributes.realm
                    else type_colors.get(node.type.value, "#888888")
                ),
                "size": 1 + (node.attributes.cost or 10) / 50  # Size based on cost
            }
            for node in nodes
        ],
        "edges": edges,
        "meta": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "realm_colors": realm_colors,
            "type_colors": type_colors
        }
    }


@router.get("/{node_id}")
async def get_node(node_id: str):
    """Get a specific node by ID."""
    node = _storage.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    return {
        "id": node.id,
        "type": node.type.value,
        "name": node.name,
        "summary": node.summary,
        "content": node.content,
        "document_ids": node.document_ids,
        "attributes": {
            "realm": node.attributes.realm.value if node.attributes.realm else None,
            "rarity": node.attributes.rarity.value if node.attributes.rarity else None,
            "cost": node.attributes.cost,
            "stats": node.attributes.stats
        },
        "image_url": node.image_url,
        "created_at": node.created_at.isoformat() if node.created_at else None,
        "updated_at": node.updated_at.isoformat() if node.updated_at else None
    }


@router.get("/{node_id}/related")
async def get_related_nodes(
    node_id: str,
    rel_type: Optional[str] = Query(None, description="Filter by relationship type")
):
    """Get nodes related to a specific node."""
    node = _storage.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Parse relationship type if provided
    relationship_type = None
    if rel_type:
        try:
            relationship_type = RelationshipType(rel_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid relationship type: {rel_type}")

    related = _storage.get_related_nodes(node_id, rel_type=relationship_type)

    return {
        "node_id": node_id,
        "related": [
            {
                "node": {
                    "id": r["node"].id,
                    "type": r["node"].type.value,
                    "name": r["node"].name,
                    "summary": r["node"].summary
                },
                "relationship": {
                    "type": r["relationship"].type.value,
                    "direction": r["direction"],
                    "weight": r["relationship"].weight
                }
            }
            for r in related
        ]
    }
