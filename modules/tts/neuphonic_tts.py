"""Neuphonic TTS implementation - High quality neural voices"""
import logging
from pathlib import Path
import os
import asyncio
import subprocess
import tempfile
import wave

from pyneuphonic import Neuphonic, TTSConfig

from models.chapter import Chapter
from modules.tts.base_tts import BaseTTS

logger = logging.getLogger(__name__)


class NeuphonicTTS(BaseTTS):
    """Neuphonic TTS provider implementation - High quality neural voices"""

    def __init__(self, voice: str = "default", speed: float = 1.0, language: str = "en"):
        super().__init__(voice, speed, language)
        self.client = None

        # Default voice mapping - None will use Neuphonic's default voice
        self.voice_id = None if voice == "default" else voice

    def _initialize_client(self):
        """Initialize Neuphonic client"""
        if self.client is None:
            try:
                # Get API key from environment variable
                api_key = os.getenv('NEUPHONIC_API_KEY')
                if not api_key:
                    raise ValueError(
                        "NEUPHONIC_API_KEY not found. Please set it:\n"
                        "export NEUPHONIC_API_KEY='your-api-key'\n"
                        "Get your key from: https://app.neuphonic.com"
                    )

                logger.info("Initializing Neuphonic TTS")
                self.client = Neuphonic(api_key=api_key)
                logger.info("Neuphonic initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Neuphonic: {e}")
                raise RuntimeError(f"Could not initialize Neuphonic TTS: {e}")

    def _convert_pcm_to_format(self, pcm_data: bytes, output_path: Path, sample_rate: int = 22050) -> None:
        """
        Convert raw PCM audio data to the desired format using ffmpeg

        Args:
            pcm_data: Raw PCM audio bytes
            output_path: Path where audio file should be saved
            sample_rate: Sample rate of the PCM data (default: 22050 Hz)
        """
        output_format = output_path.suffix.lower().lstrip('.')

        # For WAV format, we can write directly without ffmpeg
        if output_format == 'wav':
            with wave.open(str(output_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_data)
            return

        # For other formats (MP3, OGG, FLAC), use ffmpeg
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

            # First write PCM as WAV
            with wave.open(temp_wav_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_data)

        try:
            # Convert WAV to desired format using ffmpeg
            cmd = [
                'ffmpeg', '-y',  # Overwrite output file
                '-i', temp_wav_path,
                '-acodec', 'libmp3lame' if output_format == 'mp3' else output_format,
                '-ab', '128k',  # Bitrate
                str(output_path)
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            logger.debug(f"Converted PCM to {output_format.upper()} using ffmpeg")

        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg conversion failed: {e.stderr.decode()}")
            raise RuntimeError(f"Failed to convert audio to {output_format}: {e}")
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_wav_path)
            except Exception:
                pass

    async def _generate_audio_async(self, text: str, output_path: Path) -> None:
        """
        Async method to generate audio using Neuphonic SSE client

        Args:
            text: Text to convert to speech
            output_path: Path where audio file should be saved
        """
        # Create SSE client for text-to-speech
        sse = self.client.tts.AsyncSSEClient()

        # Configure TTS settings - use 22050 Hz for good quality
        tts_config = TTSConfig(
            speed=self.speed,
            voice_id=self.voice_id,
            lang_code=self.language if len(self.language) == 2 else "en",
            sampling_rate=22050  # Standard quality sampling rate
        )

        # Generate audio
        response = sse.send(text, tts_config=tts_config)

        # Collect all audio chunks (PCM data)
        audio_data = bytearray()
        async for chunk in response:
            if chunk.data.audio:
                audio_data.extend(chunk.data.audio)

        # Convert PCM to the desired format
        self._convert_pcm_to_format(bytes(audio_data), output_path, sample_rate=22050)

    def generate_audio(self, chapter: Chapter, output_path: Path) -> str:
        """
        Generate audio from chapter text using Neuphonic

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

        # Initialize client if not already done
        self._initialize_client()

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Determine output format from file extension
        output_format = output_path.suffix.lower().lstrip('.')

        try:
            logger.info(f"Generating audio for chapter {chapter.number}: {chapter.title}")
            logger.info(f"Using Neuphonic voice: {self.voice_id or 'default'}, speed: {self.speed}x")

            # Run async generation in event loop
            asyncio.run(self._generate_audio_async(chapter.text, output_path))

            # Validate output was created
            if not self._validate_output(output_path):
                raise RuntimeError(f"Failed to generate audio file for chapter {chapter.number}")

            logger.info(f"Audio saved as {output_format.upper()}: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Error generating audio for chapter {chapter.number}: {e}")
            raise RuntimeError(f"Audio generation failed for chapter {chapter.number}: {e}")
