"""Book data model"""
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path
from models.chapter import Chapter

@dataclass
class Book:
    """Represents a book with its metadata and content"""
    title: str
    author: Optional[str] = None
    file_path: Optional[Path] = None
    raw_text: str = ""
    chapters: List[Chapter] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Book('{self.title}', {len(self.chapters)} chapters)"

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the book"""
        self.chapters.append(chapter)

    def get_chapter(self, number: int) -> Optional[Chapter]:
        """Get a chapter by its number"""
        for chapter in self.chapters:
            if chapter.number == number:
                return chapter
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "author": self.author,
            "file_path": self.file_path,
            "chapters": [ch.to_dict() for ch in self.chapters]
        }