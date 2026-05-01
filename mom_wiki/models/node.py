"""Node model - a displayable unit of information for graph visualization."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid


class NodeType(str, Enum):
    """Type of content node."""
    SPELL = "spell"
    UNIT = "unit"
    ITEM = "item"
    WIZARD = "wizard"
    ABILITY = "ability"
    REALM = "realm"
    CONCEPT = "concept"
    PAGE = "page"


class Realm(str, Enum):
    """Magic realm in Master of Magic."""
    LIFE = "Life"
    DEATH = "Death"
    NATURE = "Nature"
    SORCERY = "Sorcery"
    CHAOS = "Chaos"
    ARCANE = "Arcane"


class Rarity(str, Enum):
    """Spell/item rarity."""
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    VERY_RARE = "Very Rare"


class NodeAttributes(BaseModel):
    """Attributes specific to the node type."""
    realm: Optional[Realm] = None
    cost: Optional[int] = None
    rarity: Optional[Rarity] = None
    stats: dict[str, Any] = Field(default_factory=dict)


class Node(BaseModel):
    """A displayable unit of information for graph visualization."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    name: str
    summary: str  # 1-2 sentences
    content: str  # Full description, may be markdown
    document_ids: list[str] = Field(default_factory=list)
    attributes: NodeAttributes = Field(default_factory=NodeAttributes)
    image_url: Optional[str] = None  # Drive link to sprite/icon
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat() if v else None
        }
    }

    def add_document(self, document_id: str) -> None:
        """Associate a document with this node."""
        if document_id not in self.document_ids:
            self.document_ids.append(document_id)

    def update_content(self, content: str, summary: Optional[str] = None) -> None:
        """Update the node's content."""
        self.content = content
        if summary:
            self.summary = summary
        self.updated_at = datetime.utcnow()
