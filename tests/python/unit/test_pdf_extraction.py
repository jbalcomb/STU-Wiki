"""Unit tests for the helpers in mom_wiki.scrapers.pdf_extraction.

These tests don't require a real PDF — they exercise the pure-Python
text-shaping helpers directly.
"""

from mom_wiki.scrapers.pdf_extraction import _normalize_block_text


class TestNormalizeBlockText:
    """Cover the soft-break-vs-paragraph-break logic for one PDF block."""

    def test_empty_string_returns_empty(self):
        assert _normalize_block_text("") == ""

    def test_single_line_unchanged(self):
        assert _normalize_block_text("Hello world.") == "Hello world."

    def test_multiline_prose_collapses_to_single_line(self):
        # PyMuPDF emits intra-block newlines for visual line wraps.
        # These should join with single spaces.
        text = "If you choose to start a new game\nyou are whisked to this screen.\n"
        assert _normalize_block_text(text) == (
            "If you choose to start a new game you are whisked to this screen."
        )

    def test_word_per_line_collapses_correctly(self):
        # When text wraps tightly around an image, each word becomes its
        # own line in the block. Page 13 wizard descriptions look like this.
        text = "Her \nspecial \nability \n(Charismatic) \ndoubles \nthe\neffectiveness\n"
        assert _normalize_block_text(text) == (
            "Her special ability (Charismatic) doubles the effectiveness"
        )

    def test_bullet_marker_starts_new_paragraph(self):
        # A line containing only a bullet character starts a new bullet item.
        # Adjacent bullets join with "  \n" (markdown hard break) so the list
        # reads tight, not as separate paragraphs with blank lines between.
        text = "•\nLife magic is focused on healing.\n•\nDeath magic is the opposite."
        assert _normalize_block_text(text) == (
            "• Life magic is focused on healing.  \n• Death magic is the opposite."
        )

    def test_bullet_paragraph_collapses_internal_breaks(self):
        text = (
            "•\nLife magic (indicated by white ankhs)\n"
            "is focused on healing, protective and inspirational spells.\n"
        )
        assert _normalize_block_text(text) == (
            "• Life magic (indicated by white ankhs) "
            "is focused on healing, protective and inspirational spells."
        )

    def test_intro_prose_then_bullets(self):
        # Common page 12 shape: intro sentence, then bullet list. The intro
        # paragraph is separated from the first bullet by a blank line
        # (paragraph break), but consecutive bullets join with "  \n".
        text = (
            "There are five types of magic:\n"
            "•\nLife magic is healing.\n"
            "•\nDeath magic is its opposite.\n"
        )
        assert _normalize_block_text(text) == (
            "There are five types of magic:\n\n"
            "• Life magic is healing.  \n"
            "• Death magic is its opposite."
        )

    def test_alternative_bullet_markers_recognized(self):
        # asterisk, hyphen, middle-dot all act as bullet markers.
        for marker in ("*", "-", "·"):
            text = f"{marker}\nFirst item\n{marker}\nSecond item"
            assert _normalize_block_text(text) == (
                "• First item  \n• Second item"
            ), f"failed for marker {marker!r}"

    def test_blank_lines_dropped(self):
        text = "First line.\n\n\nSecond line.\n"
        assert _normalize_block_text(text) == "First line. Second line."
