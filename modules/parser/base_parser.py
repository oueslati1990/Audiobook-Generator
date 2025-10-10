"""Base parser interface"""
from abc import ABC, abstractmethod
from pathlib import Path
from models.book import Book

class BaseParser(ABC):
    """Abstract base class for book parsers"""

    @abstractmethod
    def parse(self, base_path: Path) -> Book:
        """
        Parse a book file and return a Book object

        Args:
            file_path: Path to the book file

        Returns:
            Book object with title, author (if found), and raw text
        """
        pass

    def _extract_title_from_path(self, file_path: Path) -> str:
        """Extract title from filename as fallback"""
        return file_path.stem.replace("_", " ").replace("-", " ").title()