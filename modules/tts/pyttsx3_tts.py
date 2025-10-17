"""pyttsx3 TTS implementation (offline)"""
import logging
from pathlib import Path

import pyttsx3

from models.chapter import Chapter
from modules.tts.base_tts import BaseTTS

logger = logging.getLogger(__name__)


class Pyttsx3TTS(BaseTTS):
    """pyttsx3 TTS provider implementation (offline)"""

    def __init__(self, voice: str = "default", speed: float = 1.0, language: str = "en"):
        super().__init__(voice, speed, language)
        self._engine = None

    def _initialize_engine(self):
        """Initialize pyttsx3 engine"""
        if self._engine is None:
            try:
                logger.info("Initializing pyttsx3 TTS engine")
                self._engine = pyttsx3.init()

                # Set speech rate (words per minute)
                # Default pyttsx3 rate is ~200 wpm, but we want it slower and clearer
                # Speed 1.0 should be normal (150 wpm for better clarity)
                # Speed 1.3 = 195 wpm, Speed 0.8 = 120 wpm
                base_rate = 150  # More natural base rate
                rate = int(base_rate * self.speed)
                self._engine.setProperty('rate', rate)
                logger.info(f"Speech rate set to: {rate} wpm (speed multiplier: {self.speed}x)")

                # Set volume to maximum for better clarity
                self._engine.setProperty('volume', 1.0)

                # Try to find and use a better quality voice
                voices = self._engine.getProperty('voices')

                if self.voice != "default":
                    # User specified a voice
                    for v in voices:
                        if self.voice in v.id or self.voice in v.name:
                            self._engine.setProperty('voice', v.id)
                            logger.info(f"Using voice: {v.name}")
                            break
                else:
                    # Try to find a better quality voice (prefer female voices, often clearer)
                    # Look for voices with "english" and prefer those with "female" or quality indicators
                    best_voice = None

                    for v in voices:
                        voice_name = v.name.lower()
                        voice_id = v.id.lower()

                        # Prefer english voices
                        if 'english' in voice_name or 'english' in voice_id or 'en' in voice_id:
                            # Prefer female voices (often clearer) or quality voices
                            if 'female' in voice_name or 'aria' in voice_name or 'zira' in voice_name:
                                best_voice = v
                                break
                            elif best_voice is None:
                                best_voice = v

                    if best_voice:
                        self._engine.setProperty('voice', best_voice.id)
                        logger.info(f"Using voice: {best_voice.name}")
                    else:
                        logger.info(f"Using default system voice")

                logger.info("pyttsx3 engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
                raise RuntimeError(f"Could not initialize pyttsx3: {e}")

    def generate_audio(self, chapter: Chapter, output_path: Path) -> str:
        """
        Generate audio from chapter text using pyttsx3

        Args:
            chapter: Chapter object with text to convert
            output_path: Path where audio file should be saved (with extension)

        Returns:
            Path to generated audio file

        Raises:
            RuntimeError: If audio generation fails
            ValueError: If chapter has no text
        """
        if not chapter.text or len(chapter.text.strip()) == 0:
            raise ValueError(f"Chapter {chapter.number} has no text to convert")

        # Initialize engine if not already done
        self._initialize_engine()

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine output format from file extension
        output_format = output_path.suffix.lower().lstrip('.')

        # pyttsx3 can save directly to MP3 or WAV
        if output_format not in ['mp3', 'wav']:
            logger.warning(f"Format {output_format} not directly supported by pyttsx3, using MP3")
            output_format = 'mp3'
            output_path = output_path.with_suffix('.mp3')

        try:
            logger.info(f"Generating audio for chapter {chapter.number}: {chapter.title}")

            # Save to file
            self._engine.save_to_file(chapter.text, str(output_path))
            self._engine.runAndWait()

            # pyttsx3 may need a moment to flush the file to disk
            import time
            max_wait = 5  # Maximum 5 seconds
            wait_interval = 0.5  # Check every 0.5 seconds
            elapsed = 0

            while elapsed < max_wait:
                if self._validate_output(output_path):
                    break
                time.sleep(wait_interval)
                elapsed += wait_interval

            # Final validation
            if not self._validate_output(output_path):
                raise RuntimeError(f"Failed to generate audio file for chapter {chapter.number}")

            logger.info(f"Audio saved as {output_format.upper()}: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating audio for chapter {chapter.number}: {e}")
            raise RuntimeError(f"Audio generation failed for chapter {chapter.number}: {e}")
