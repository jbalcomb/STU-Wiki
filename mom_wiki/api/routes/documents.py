"""Document API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ...storage import CorpusStorage

router = APIRouter(prefix="/documents", tags=["documents"])

_storage = CorpusStorage()


@router.get("")
async def list_documents(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """List all documents with optional filtering."""
    documents = _storage.list_documents(source_id=source_id)

    # Pagination
    total = len(documents)
    documents = documents[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "documents": [
            {
                "id": doc.id,
                "source_id": doc.source_id,
                "title": doc.title,
                "url": doc.url,
                "file_path": doc.file_path,
                "extracted_at": doc.extracted_at.isoformat() if doc.extracted_at else None,
                "node_ids": doc.node_ids,
                "metadata": {
                    "tags": doc.metadata.tags,
                    "author": doc.metadata.author
                }
            }
            for doc in documents
        ]
    }


@router.get("/{document_id}")
async def get_document(document_id: str, include_content: bool = Query(True)):
    """Get a specific document by ID."""
    doc = _storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    result = {
        "id": doc.id,
        "source_id": doc.source_id,
        "title": doc.title,
        "content_path": doc.content_path,
        "url": doc.url,
        "file_path": doc.file_path,
        "drive_url": doc.drive_url,
        "extracted_at": doc.extracted_at.isoformat() if doc.extracted_at else None,
        "checksum": doc.checksum,
        "node_ids": doc.node_ids,
        "metadata": {
            "tags": doc.metadata.tags,
            "author": doc.metadata.author,
            "publish_date": doc.metadata.publish_date,
            "custom": doc.metadata.custom
        }
    }

    if include_content:
        content = _storage.get_document_content(document_id)
        result["content"] = content

    return result


@router.get("/{document_id}/content")
async def get_document_content(document_id: str):
    """Get the raw markdown content of a document."""
    doc = _storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    content = _storage.get_document_content(document_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found")

    return {"content": content}


@router.get("/{document_id}/nodes")
async def get_document_nodes(document_id: str):
    """Get all nodes associated with a document."""
    doc = _storage.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    nodes = []
    for node_id in doc.node_ids:
        node = _storage.get_node(node_id)
        if node:
            nodes.append({
                "id": node.id,
                "type": node.type.value,
                "name": node.name,
                "summary": node.summary
            })

    return {"document_id": document_id, "nodes": nodes}
