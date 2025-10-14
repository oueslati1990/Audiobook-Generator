"""Coqui TTS implementation"""
import logging
from pathlib import Path
from typing import Optional

from TTS.api import TTS
from pydub import AudioSegment

from models.chapter import Chapter
from modules.tts.base_tts import BaseTTS

logger = logging.getLogger(__name__)


class CoquiTTS(BaseTTS):
    """Coqui TTS provider implementation"""

    def __init__(self, voice: str = "default", speed: float = 1.0, language: str = "en"):
        super().__init__(voice, speed, language)
        self._tts_model: Optional[TTS] = None
        self.model_name = "tts_models/en/ljspeech/tacotron2-DDC"

    def _load_model(self):
        """Lazy load TTS model to avoid startup delay"""
        if self._tts_model is None:
            try:
                logger.info(f"Loading Coqui TTS model: {self.model_name}")
                self._tts_model = TTS(model_name=self.model_name)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load TTS model: {e}")
                raise RuntimeError(f"Could not initialize Coqui TTS: {e}")
    
    def generate_audio(self, chapter: Chapter, output_path: Path) -> str:
        """
        Generate audio from chapter text using Coqui TTS

        Args:
            chapter: Chapter object with text to convert
            output_path: Path where audio file should be saved (with extension)

        Returns:
            Path to generated audio file

        Raises:
            RuntimeError: If model loading or audio generation fails
            ValueError: If chapter has no text
        """
        if not chapter.text or len(chapter.text.strip()) == 0:
            raise ValueError(f"Chapter {chapter.number} has no text to convert")

        # Load model if not already loaded
        self._load_model()

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine output format from file extension
        output_format = output_path.suffix.lower().lstrip('.')

        # Generate to temporary WAV file (Coqui outputs WAV)
        temp_wav_path = output_path.with_suffix('.temp.wav')

        try:
            logger.info(f"Generating audio for chapter {chapter.number}: {chapter.title}")

            # Generate audio with Coqui TTS
            self._tts_model.tts_to_file(
                text=chapter.text,
                file_path=str(temp_wav_path)
            )

            # Validate WAV was created
            if not self._validate_output(temp_wav_path):
                raise RuntimeError(f"Failed to generate WAV file for chapter {chapter.number}")

            # Convert to final format (default MP3)
            if output_format == 'wav':
                # Just rename temp file to final file
                temp_wav_path.rename(output_path)
                logger.info(f"Audio saved as WAV: {output_path}")
            else:
                # Convert WAV to requested format (default MP3)
                try:
                    audio = AudioSegment.from_wav(str(temp_wav_path))

                    # Export with format-specific settings
                    export_params = {}
                    if output_format == 'mp3':
                        export_params['bitrate'] = '128k'  # Can be made configurable

                    audio.export(str(output_path), format=output_format, **export_params)
                    logger.info(f"Audio converted and saved as {output_format.upper()}: {output_path}")

                except Exception as e:
                    raise RuntimeError(f"Failed to convert audio to {output_format}: {e}")
                finally:
                    # Clean up temp WAV file
                    if temp_wav_path.exists():
                        temp_wav_path.unlink()

            # Final validation
            if not self._validate_output(output_path):
                raise RuntimeError(f"Output file validation failed: {output_path}")

            return str(output_path)

        except Exception as e:
            # Clean up on error
            if temp_wav_path.exists():
                temp_wav_path.unlink()

            logger.error(f"Error generating audio for chapter {chapter.number}: {e}")
            raise RuntimeError(f"Audio generation failed for chapter {chapter.number}: {e}")