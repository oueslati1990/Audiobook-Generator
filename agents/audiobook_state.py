from typing import TypedDict, Optional

from ..models.config import AudiobookConfig
from ..models.book import Book

class AudiobookState(TypedDict):
    """State that flows through the workflow"""
    book_path: str
    book: Optional[Book]
    config: AudiobookConfig
    output_dir: str
    error: Optional[str]
