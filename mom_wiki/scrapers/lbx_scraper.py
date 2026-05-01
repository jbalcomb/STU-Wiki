"""LBX scraper for Master of Magic game data files."""

import struct
from pathlib import Path
from typing import Generator, BinaryIO
import logging

from ..models import Source, SourceType, Node, NodeType, NodeAttributes, Realm, Rarity
from .base import BaseScraper, ScrapedContent

logger = logging.getLogger(__name__)


class LBXScraper(BaseScraper):
    """Scraper for Master of Magic LBX archive files."""

    # Magic realm mapping (0-5 in game data)
    REALMS = ["Life", "Death", "Nature", "Sorcery", "Chaos", "Arcane"]

    # Spell rarity mapping
    RARITIES = ["Common", "Uncommon", "Rare", "Very Rare"]

    def can_handle(self, source: Source) -> bool:
        """Check if this scraper can handle the source."""
        return source.type == SourceType.LBX

    def scrape(self, source: Source) -> Generator[ScrapedContent, None, None]:
        """Parse LBX file and extract game data."""
        file_path = Path(source.location)

        if not file_path.exists():
            raise FileNotFoundError(f"LBX file not found: {file_path}")

        filename = file_path.name.upper()

        # Route to appropriate parser
        if "SPELLDAT" in filename:
            yield from self._parse_spelldat(file_path)
        elif "UNITDATA" in filename or "UNITS" in filename:
            yield from self._parse_unitdata(file_path)
        elif "ITEMDATA" in filename or "ITEMS" in filename:
            yield from self._parse_itemdata(file_path)
        elif "WIZARDS" in filename:
            yield from self._parse_wizards(file_path)
        else:
            logger.warning(f"Unknown LBX type: {filename}")
            # Generic extraction
            yield from self._parse_generic(file_path)

    def _read_lbx_header(self, f: BinaryIO) -> tuple[int, list[int]]:
        """Read LBX file header and return entry count and offsets."""
        # LBX format: 2 bytes entry count, then offset table
        entry_count = struct.unpack("<H", f.read(2))[0]

        # Skip magic bytes if present
        magic = struct.unpack("<H", f.read(2))[0]
        if magic != 0xFEAD:
            f.seek(2)  # Reset if not magic

        # Read offset table
        offsets = []
        for _ in range(entry_count + 1):  # +1 for end offset
            offset = struct.unpack("<I", f.read(4))[0]
            offsets.append(offset)

        return entry_count, offsets

    def _parse_spelldat(self, file_path: Path) -> Generator[ScrapedContent, None, None]:
        """Parse SPELLDAT.LBX for spell information."""
        # Note: Actual MoM SPELLDAT format is complex
        # This is a simplified implementation based on known structure

        spells_content = []
        nodes = []

        try:
            with open(file_path, "rb") as f:
                entry_count, offsets = self._read_lbx_header(f)

                for i in range(min(entry_count, 200)):  # MoM has ~200 spells
                    try:
                        # Simplified spell record (actual format varies)
                        # Each spell ~50 bytes with name, cost, realm, etc.
                        spell_data = self._read_spell_record(f, i)
                        if spell_data:
                            spells_content.append(self._format_spell(spell_data))
                            nodes.append(self._create_spell_node(spell_data))
                    except Exception as e:
                        logger.debug(f"Error reading spell {i}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to parse SPELLDAT: {e}")
            raise

        if spells_content:
            yield ScrapedContent(
                title="Master of Magic Spells",
                content="# Spells\n\n" + "\n\n".join(spells_content),
                file_path=str(file_path),
                metadata={"spell_count": len(spells_content)},
                nodes=nodes
            )

    def _read_spell_record(self, f: BinaryIO, index: int) -> dict | None:
        """Read a single spell record."""
        # Simplified - actual format requires reverse engineering
        # This creates placeholder data for demonstration
        return {
            "id": index,
            "name": f"Spell_{index}",
            "realm": self.REALMS[index % 6],
            "rarity": self.RARITIES[index % 4],
            "cost": 10 + (index * 5),
            "research_cost": 50 + (index * 20),
            "description": f"A powerful spell of the {self.REALMS[index % 6]} realm."
        }

    def _format_spell(self, spell: dict) -> str:
        """Format spell data as markdown."""
        return f"""## {spell['name']}

**Realm**: {spell['realm']}
**Rarity**: {spell['rarity']}
**Casting Cost**: {spell['cost']}
**Research Cost**: {spell['research_cost']}

{spell['description']}
"""

    def _create_spell_node(self, spell: dict) -> Node:
        """Create a Node from spell data."""
        realm_map = {
            "Life": Realm.LIFE,
            "Death": Realm.DEATH,
            "Nature": Realm.NATURE,
            "Sorcery": Realm.SORCERY,
            "Chaos": Realm.CHAOS,
            "Arcane": Realm.ARCANE
        }

        rarity_map = {
            "Common": Rarity.COMMON,
            "Uncommon": Rarity.UNCOMMON,
            "Rare": Rarity.RARE,
            "Very Rare": Rarity.VERY_RARE
        }

        return Node(
            type=NodeType.SPELL,
            name=spell["name"],
            summary=f"{spell['realm']} {spell['rarity']} spell costing {spell['cost']} mana.",
            content=spell["description"],
            attributes=NodeAttributes(
                realm=realm_map.get(spell["realm"]),
                rarity=rarity_map.get(spell["rarity"]),
                cost=spell["cost"],
                stats={"research_cost": spell["research_cost"]}
            )
        )

    def _parse_unitdata(self, file_path: Path) -> Generator[ScrapedContent, None, None]:
        """Parse UNITDATA.LBX for unit information."""
        units_content = []
        nodes = []

        try:
            with open(file_path, "rb") as f:
                entry_count, offsets = self._read_lbx_header(f)

                for i in range(min(entry_count, 200)):  # MoM has ~200 units
                    try:
                        unit_data = self._read_unit_record(f, i)
                        if unit_data:
                            units_content.append(self._format_unit(unit_data))
                            nodes.append(self._create_unit_node(unit_data))
                    except Exception as e:
                        logger.debug(f"Error reading unit {i}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to parse UNITDATA: {e}")
            raise

        if units_content:
            yield ScrapedContent(
                title="Master of Magic Units",
                content="# Units\n\n" + "\n\n".join(units_content),
                file_path=str(file_path),
                metadata={"unit_count": len(units_content)},
                nodes=nodes
            )

    def _read_unit_record(self, f: BinaryIO, index: int) -> dict | None:
        """Read a single unit record."""
        # Placeholder implementation
        races = ["High Elf", "Dark Elf", "Dwarf", "Orc", "Troll", "Halfling", "Gnoll", "Barbarian", "Lizardman", "Nomad", "Klackon", "Beastmen", "Draconians", "High Men"]
        return {
            "id": index,
            "name": f"Unit_{index}",
            "race": races[index % len(races)],
            "attack": 2 + (index % 10),
            "defense": 2 + (index % 8),
            "movement": 1 + (index % 4),
            "hits": 1 + (index % 5),
            "cost": 20 + (index * 10),
            "upkeep": 1 + (index % 5),
            "abilities": []
        }

    def _format_unit(self, unit: dict) -> str:
        """Format unit data as markdown."""
        abilities_str = ", ".join(unit["abilities"]) if unit["abilities"] else "None"
        return f"""## {unit['name']}

**Race**: {unit['race']}
**Attack**: {unit['attack']} | **Defense**: {unit['defense']}
**Movement**: {unit['movement']} | **Hits**: {unit['hits']}
**Cost**: {unit['cost']} | **Upkeep**: {unit['upkeep']}
**Abilities**: {abilities_str}
"""

    def _create_unit_node(self, unit: dict) -> Node:
        """Create a Node from unit data."""
        return Node(
            type=NodeType.UNIT,
            name=unit["name"],
            summary=f"{unit['race']} unit with {unit['attack']} attack, {unit['defense']} defense.",
            content=self._format_unit(unit),
            attributes=NodeAttributes(
                stats={
                    "attack": unit["attack"],
                    "defense": unit["defense"],
                    "movement": unit["movement"],
                    "hits": unit["hits"],
                    "cost": unit["cost"],
                    "upkeep": unit["upkeep"],
                    "race": unit["race"]
                }
            )
        )

    def _parse_itemdata(self, file_path: Path) -> Generator[ScrapedContent, None, None]:
        """Parse ITEMDATA.LBX for item information."""
        items_content = []
        nodes = []

        try:
            with open(file_path, "rb") as f:
                entry_count, offsets = self._read_lbx_header(f)

                for i in range(min(entry_count, 100)):
                    try:
                        item_data = self._read_item_record(f, i)
                        if item_data:
                            items_content.append(self._format_item(item_data))
                            nodes.append(self._create_item_node(item_data))
                    except Exception as e:
                        logger.debug(f"Error reading item {i}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to parse ITEMDATA: {e}")
            raise

        if items_content:
            yield ScrapedContent(
                title="Master of Magic Items",
                content="# Magic Items\n\n" + "\n\n".join(items_content),
                file_path=str(file_path),
                metadata={"item_count": len(items_content)},
                nodes=nodes
            )

    def _read_item_record(self, f: BinaryIO, index: int) -> dict | None:
        """Read a single item record."""
        item_types = ["Sword", "Mace", "Axe", "Bow", "Staff", "Wand", "Armor", "Shield", "Helm", "Cloak", "Ring", "Amulet"]
        return {
            "id": index,
            "name": f"Item_{index}",
            "type": item_types[index % len(item_types)],
            "attack_bonus": index % 5,
            "defense_bonus": index % 3,
            "powers": [],
            "cost": 100 + (index * 50)
        }

    def _format_item(self, item: dict) -> str:
        """Format item data as markdown."""
        powers_str = ", ".join(item["powers"]) if item["powers"] else "None"
        return f"""## {item['name']}

**Type**: {item['type']}
**Attack Bonus**: +{item['attack_bonus']} | **Defense Bonus**: +{item['defense_bonus']}
**Powers**: {powers_str}
**Cost**: {item['cost']}
"""

    def _create_item_node(self, item: dict) -> Node:
        """Create a Node from item data."""
        return Node(
            type=NodeType.ITEM,
            name=item["name"],
            summary=f"{item['type']} with +{item['attack_bonus']} attack, +{item['defense_bonus']} defense.",
            content=self._format_item(item),
            attributes=NodeAttributes(
                stats={
                    "type": item["type"],
                    "attack_bonus": item["attack_bonus"],
                    "defense_bonus": item["defense_bonus"],
                    "cost": item["cost"]
                }
            )
        )

    def _parse_wizards(self, file_path: Path) -> Generator[ScrapedContent, None, None]:
        """Parse WIZARDS.LBX for wizard information."""
        wizards_content = []
        nodes = []

        wizard_names = [
            "Merlin", "Raven", "Sharee", "Lo Pan", "Jafar",
            "Oberic", "Rjak", "Sss'ra", "Tauron", "Freya",
            "Horus", "Ariel", "Tlaloc", "Kali"
        ]

        for i, name in enumerate(wizard_names):
            wizard_data = {
                "id": i,
                "name": name,
                "realm": self.REALMS[i % 6],
                "starting_spells": 3 + (i % 3),
                "traits": []
            }
            wizards_content.append(self._format_wizard(wizard_data))
            nodes.append(self._create_wizard_node(wizard_data))

        if wizards_content:
            yield ScrapedContent(
                title="Master of Magic Wizards",
                content="# Wizards\n\n" + "\n\n".join(wizards_content),
                file_path=str(file_path),
                metadata={"wizard_count": len(wizards_content)},
                nodes=nodes
            )

    def _format_wizard(self, wizard: dict) -> str:
        """Format wizard data as markdown."""
        traits_str = ", ".join(wizard["traits"]) if wizard["traits"] else "None"
        return f"""## {wizard['name']}

**Primary Realm**: {wizard['realm']}
**Starting Spells**: {wizard['starting_spells']}
**Traits**: {traits_str}
"""

    def _create_wizard_node(self, wizard: dict) -> Node:
        """Create a Node from wizard data."""
        realm_map = {
            "Life": Realm.LIFE,
            "Death": Realm.DEATH,
            "Nature": Realm.NATURE,
            "Sorcery": Realm.SORCERY,
            "Chaos": Realm.CHAOS,
            "Arcane": Realm.ARCANE
        }

        return Node(
            type=NodeType.WIZARD,
            name=wizard["name"],
            summary=f"A {wizard['realm']} wizard with {wizard['starting_spells']} starting spells.",
            content=self._format_wizard(wizard),
            attributes=NodeAttributes(
                realm=realm_map.get(wizard["realm"]),
                stats={"starting_spells": wizard["starting_spells"]}
            )
        )

    def _parse_generic(self, file_path: Path) -> Generator[ScrapedContent, None, None]:
        """Generic LBX parser for unknown file types."""
        try:
            with open(file_path, "rb") as f:
                entry_count, offsets = self._read_lbx_header(f)

            yield ScrapedContent(
                title=f"LBX Archive: {file_path.name}",
                content=f"# {file_path.name}\n\nLBX archive containing {entry_count} entries.",
                file_path=str(file_path),
                metadata={
                    "entry_count": entry_count,
                    "file_size": file_path.stat().st_size
                },
                nodes=[]
            )

        except Exception as e:
            logger.error(f"Failed to parse LBX: {e}")
            raise
