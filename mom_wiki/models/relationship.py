"""Relationship model - typed connection between nodes."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field
import uuid


class RelationshipType(str, Enum):
    """Type of relationship between nodes."""
    BELONGS_TO = "belongs_to"  # Spell belongs to realm, unit belongs to race
    HAS_ABILITY = "has_ability"  # Unit has ability
    REQUIRES = "requires"  # Spell requires research, item requires crafting
    COUNTERS = "counters"  # Spell counters another spell
    REFERENCES = "references"  # Document references another
    RELATED_TO = "related_to"  # General association


class Relationship(BaseModel):
    """A typed connection between nodes."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str
    target_node_id: str
    type: RelationshipType
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __hash__(self) -> int:
        """Make relationship hashable for dedup."""
        return hash((self.source_node_id, self.target_node_id, self.type))

    def __eq__(self, other: object) -> bool:
        """Check equality based on nodes and type."""
        if not isinstance(other, Relationship):
            return False
        return (
            self.source_node_id == other.source_node_id
            and self.target_node_id == other.target_node_id
            and self.type == other.type
        )
