import re
from typing import List

from models.book import Book
from models.chapter import Chapter
from models.config import ChapterDetectionConfig


class ChapterSplitter:
    """Splits book text into chapters using regex patterns"""

    def __init__(self, config: ChapterDetectionConfig):
        self.config = config

    def split(self, book: Book) -> List[Chapter]:
        """
        Split book text into chapters

        Args:
            book: Book object with raw_text

        Returns:
            List of Chapter objects
        """
        if not book.raw_text:
            raise ValueError("Book has no text to split")
        
        pattern = self.config.pattern
        matches = list(re.finditer(pattern, book.raw_text, re.MULTILINE | re.IGNORECASE))

        if not matches:
            # no chapters, treat all book as one chapter
            return [Chapter(
                number=1,
                text=book.raw_text,
                title="Full book"
            )]
        
        chapters = []

        for i, match in enumerate(matches):
            chapter_number = i + 1
            chapter_title = match.group(0).strip()

            # Extract chapter text (from this match to next match or end)
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(book.raw_text)
            chapter_text = book.raw_text[start_pos:end_pos].strip()

            chapters.append(Chapter(
                number=chapter_number,
                title=chapter_title,
                text=chapter_text
            ))

        return chapters
        
    def split_and_update_book(self, book: Book) -> Book:
        """
        Split book into chapters and update the book object

        Args:
            book: Book object to split

        Returns:
            Updated Book object with chapters
        """
        chapters = self.split(book)
        book.chapters = chapters
        return book
        