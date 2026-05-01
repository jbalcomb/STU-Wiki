"""Web scraper for HTML pages."""

import time
from typing import Generator
from urllib.parse import urljoin, urlparse
import logging

import requests
from bs4 import BeautifulSoup

from ..models import Source, SourceType, Node, NodeType
from .base import BaseScraper, ScrapedContent

logger = logging.getLogger(__name__)


class WebScraper(BaseScraper):
    """Scraper for web pages using BeautifulSoup."""

    def __init__(self, storage, rate_limit: float = 1.0, user_agent: str = None):
        super().__init__(storage)
        self.rate_limit = rate_limit
        self.user_agent = user_agent or "MoMWikiCorpus/0.1.0"
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def can_handle(self, source: Source) -> bool:
        """Check if this scraper can handle the source."""
        return source.type == SourceType.WEB

    def scrape(self, source: Source) -> Generator[ScrapedContent, None, None]:
        """Scrape content from a web source."""
        url = source.location

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract main content
        content = self._extract_content(soup)
        title = self._extract_title(soup, url)

        # Create node from page
        node = self._create_node_from_page(soup, title, content)

        yield ScrapedContent(
            title=title,
            content=content,
            url=url,
            metadata={
                "tags": self._extract_tags(soup),
            },
            nodes=[node] if node else []
        )

        # Rate limiting
        time.sleep(self.rate_limit)

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title."""
        # Try various title sources
        if soup.title:
            title = soup.title.string
            if title:
                # Clean up common suffixes
                for suffix in [" | Master of Magic Wiki", " - Fandom", " Wiki"]:
                    if title.endswith(suffix):
                        title = title[:-len(suffix)]
                return title.strip()

        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        # Fallback to URL path
        path = urlparse(url).path
        return path.split("/")[-1].replace("_", " ") or "Untitled"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content as markdown."""
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "aside"]):
            element.decompose()

        # Try to find main content area
        main = soup.find("main") or soup.find("article") or soup.find(class_="mw-parser-output")
        if main:
            soup = main

        # Convert to markdown-like format
        lines = []

        for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
            if element.name.startswith("h"):
                level = int(element.name[1])
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"{'#' * level} {text}\n")
            elif element.name == "p":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"{text}\n")
            elif element.name == "li":
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"- {text}")
            elif element.name == "table":
                # Simple table extraction
                lines.append(self._extract_table(element))

        return "\n".join(lines)

    def _extract_table(self, table) -> str:
        """Extract table as markdown."""
        rows = table.find_all("tr")
        if not rows:
            return ""

        md_lines = []
        for i, row in enumerate(rows):
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            md_lines.append("| " + " | ".join(cell_texts) + " |")

            # Add separator after header
            if i == 0 and row.find("th"):
                md_lines.append("| " + " | ".join(["---"] * len(cells)) + " |")

        return "\n".join(md_lines) + "\n"

    def _extract_tags(self, soup: BeautifulSoup) -> list[str]:
        """Extract tags/categories from page."""
        tags = []

        # Look for category links (common in wikis)
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if "/Category:" in href or "/category/" in href.lower():
                tag = link.get_text(strip=True)
                if tag and tag not in tags:
                    tags.append(tag)

        return tags[:10]  # Limit to 10 tags

    def _create_node_from_page(self, soup: BeautifulSoup, title: str, content: str) -> Node:
        """Create a Node from the scraped page."""
        # Determine node type from content/title
        node_type = self._infer_node_type(title, content)

        # Extract first paragraph as summary
        first_p = soup.find("p")
        summary = first_p.get_text(strip=True)[:200] if first_p else title

        return Node(
            type=node_type,
            name=title,
            summary=summary,
            content=content
        )

    def _infer_node_type(self, title: str, content: str) -> NodeType:
        """Infer the node type from title and content."""
        title_lower = title.lower()
        content_lower = content.lower()

        # Check for specific types
        if any(word in title_lower for word in ["spell", "magic", "enchant"]):
            return NodeType.SPELL
        if any(word in title_lower for word in ["unit", "creature", "troop"]):
            return NodeType.UNIT
        if any(word in title_lower for word in ["item", "artifact", "equipment"]):
            return NodeType.ITEM
        if any(word in title_lower for word in ["wizard", "mage"]):
            return NodeType.WIZARD
        if any(word in title_lower for word in ["ability", "skill"]):
            return NodeType.ABILITY
        if title_lower in ["life", "death", "nature", "sorcery", "chaos", "arcane"]:
            return NodeType.REALM

        # Default to generic page
        return NodeType.PAGE
