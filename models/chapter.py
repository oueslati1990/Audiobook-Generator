"""Chapter data model"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Chapter:
    """Represents a single chapter in the book"""
    number: int
    title: str
    text: str
    audio_path: Optional[str] = None
    duration: Optional[float] = None  # in seconds

    def __repr__(self) -> str:
        return f"Chapter({self.number} : {self.title})"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "number": self.number,
            "title": self.title,
            "text": self.text,
            "audio_path": self.audio_path,
            "duration": self.duration
        }