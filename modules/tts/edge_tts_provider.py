"""Edge TTS implementation"""
import logging
import asyncio
import subprocess
from pathlib import Path

import edge_tts

from models.chapter import Chapter
from modules.tts.base_tts import BaseTTS

logger = logging.getLogger(__name__)


class EdgeTTS(BaseTTS):
    """Edge TTS provider implementation"""

    def __init__(self, voice: str = "default", speed: float = 1.0, language: str = "en"):
        super().__init__(voice, speed, language)
        # Map common language codes to Edge TTS voices
        self.voice_map = {
            "en": "en-US-AriaNeural",
            "en-US": "en-US-AriaNeural",
            "en-GB": "en-GB-SoniaNeural",
            "default": "en-US-AriaNeural"
        }
        # Use provided voice or map from language
        self.edge_voice = voice if voice != "default" else self.voice_map.get(language, "en-US-AriaNeural")

    async def _generate_audio_async(self, text: str, output_path: Path) -> None:
        """Asynchronously generate audio using Edge TTS"""
        try:
            # Calculate rate for speed adjustment (Edge TTS uses percentage)
            # speed 1.0 = 0%, speed 1.5 = +50%, speed 0.5 = -50%
            rate = f"{int((self.speed - 1.0) * 100):+d}%"

            communicate = edge_tts.Communicate(text, self.edge_voice, rate=rate)
            await communicate.save(str(output_path))

        except Exception as e:
            logger.error(f"Edge TTS generation failed: {e}")
            raise RuntimeError(f"Could not generate audio with Edge TTS: {e}")
    
    def generate_audio(self, chapter: Chapter, output_path: Path) -> str:
        """
        Generate audio from chapter text using Edge TTS

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

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine output format from file extension
        output_format = output_path.suffix.lower().lstrip('.')

        # Edge TTS generates MP3 by default, we'll use a temp file
        temp_mp3_path = output_path.with_suffix('.temp.mp3')

        try:
            logger.info(f"Generating audio for chapter {chapter.number}: {chapter.title}")

            # Generate audio with Edge TTS (run async function in sync context)
            asyncio.run(self._generate_audio_async(chapter.text, temp_mp3_path))

            # Validate MP3 was created
            if not self._validate_output(temp_mp3_path):
                raise RuntimeError(f"Failed to generate MP3 file for chapter {chapter.number}")

            # Convert to final format if needed
            if output_format == 'mp3':
                # Just rename temp file to final file
                temp_mp3_path.rename(output_path)
                logger.info(f"Audio saved as MP3: {output_path}")
            else:
                # Convert MP3 to requested format using ffmpeg
                try:
                    logger.info(f"Converting MP3 to {output_format.upper()}...")

                    # Build ffmpeg command
                    cmd = ['ffmpeg', '-i', str(temp_mp3_path), '-y']

                    # Add format-specific options
                    if output_format == 'wav':
                        cmd.extend(['-acodec', 'pcm_s16le'])
                    elif output_format == 'ogg':
                        cmd.extend(['-acodec', 'libvorbis'])
                    elif output_format == 'flac':
                        cmd.extend(['-acodec', 'flac'])

                    cmd.append(str(output_path))

                    # Run ffmpeg conversion
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )

                    if result.returncode != 0:
                        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

                    logger.info(f"Audio converted and saved as {output_format.upper()}: {output_path}")

                except FileNotFoundError:
                    raise RuntimeError(
                        "ffmpeg not found. Please install ffmpeg to convert to formats other than MP3. "
                        "Install with: sudo dnf install ffmpeg"
                    )
                except Exception as e:
                    raise RuntimeError(f"Failed to convert audio to {output_format}: {e}")
                finally:
                    # Clean up temp MP3 file
                    if temp_mp3_path.exists():
                        temp_mp3_path.unlink()

            # Final validation
            if not self._validate_output(output_path):
                raise RuntimeError(f"Output file validation failed: {output_path}")

            return str(output_path)

        except Exception as e:
            # Clean up on error
            if temp_mp3_path.exists():
                temp_mp3_path.unlink()

            logger.error(f"Error generating audio for chapter {chapter.number}: {e}")
            raise RuntimeError(f"Audio generation failed for chapter {chapter.number}: {e}")