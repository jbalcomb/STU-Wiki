"""Storage modules for Master of Magic Wiki Corpus."""

from .corpus import CorpusStorage, SaveResult
from .drive import DriveStorage

__all__ = ["CorpusStorage", "SaveResult", "DriveStorage"]
