"""Scraper modules for Master of Magic Wiki Corpus."""

from ..models import Source, SourceType
from ..storage import CorpusStorage
from .base import BaseScraper, ScrapedContent
from .web_scraper import WebScraper
from .pdf_scraper import PDFScraper
from .lbx_scraper import LBXScraper


def get_scraper(source: Source, storage: CorpusStorage) -> BaseScraper:
    """Factory function to get the appropriate scraper for a source."""
    scrapers = [
        WebScraper(storage),
        PDFScraper(storage),
        LBXScraper(storage),
    ]

    for scraper in scrapers:
        if scraper.can_handle(source):
            return scraper

    raise ValueError(f"No scraper available for source type: {source.type}")


__all__ = [
    "BaseScraper",
    "ScrapedContent",
    "WebScraper",
    "PDFScraper",
    "LBXScraper",
    "get_scraper",
]
