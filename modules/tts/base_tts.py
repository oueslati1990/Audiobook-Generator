"""Base TTS interface"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from models.chapter import Chapter


class BaseTTS(ABC):
    """Abstract base class for TTS providers"""

    def __init__(self, voice: str = "default", speed: float = 1.0, language: str = "en"):
        self.voice = voice
        self.speed = speed
        self.language = language

    @abstractmethod
    def generate_audio(self, chapter: Chapter, output_path:str) -> str:
        """
        Generate audio from chapter text

        Args:
            chapter: Chapter object with text to convert
            output_path: Path where audio file should be saved

        Returns:
            Path to generated audio file
        """
        pass

    def _validate_output(self, output_path: Path) -> bool:
        """
        Validate that audio file was created successfully

        Args:
            output_path: Path to check

        Returns:
            True if file exists and has content
        """
        return output_path.exists() and output_path.stat().st_size > 0
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats

        Returns:
            List of format extensions (e.g., ['mp3', 'wav'])
        """
        return ["wav", "mp3"]