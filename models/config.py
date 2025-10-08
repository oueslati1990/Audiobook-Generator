"""Configuration model"""

from dataclasses import dataclass
from typing import Literal
from pathlib import Path

@dataclass
class TTSConfig:
    """TTS provider configuration"""
    provider: Literal["coqui", "neuphonic", "openai"] = "coqui"
    voice: str = "default"
    speed: float = 1.0
    language: str = "en"

@dataclass
class OutputConfig:
    """Output Configuration"""
    format: Literal["mp3", "wav"] = "mp3"
    bitrate: str = "128k"
    directory: Path = Path("./audiobooks")

@dataclass
class ChapterDetectionConfig:
    """Chapter Detection Configuration"""
    method: Literal["regex", "ai"] = "regex"
    pattern: str = r"^Chapter \d+"

@dataclass
class AudiobookConfig:
    """Main configuration for audiobook generation"""
    tts : TTSConfig = None
    output: OutputConfig = None
    chapter_detection: ChapterDetectionConfig = None

    def __post_init__(self):
        if self.tts == None:
            self.tts = TTSConfig()
        if self.output == None:
            self.output = OutputConfig()
        if self.chapter_detection == None:
            self.chapter_detection = ChapterDetectionConfig()

    @classmethod
    def from_dict(cls, config_dict: dict) -> "AudiobookConfig":
        """Create config from dictionary"""
        tts_config = TTSConfig(**config_dict.get("tts", {}))
        output_Config = OutputConfig(**config_dict.get("output", {}))
        chapter_detection_config = ChapterDetectionConfig(**config_dict.get("chapter_detection", {}))

        return cls(
            tts = tts_config,
            output = output_Config,
            chapter_detection = chapter_detection_config
        ) 
    