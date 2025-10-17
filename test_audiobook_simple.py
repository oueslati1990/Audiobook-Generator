#!/usr/bin/env python3
"""Simple test script for audiobook generation using offline TTS (pyttsx3)"""

import logging
from pathlib import Path
from langgraph.graph import StateGraph, END

from agents.audiobook_state import AudiobookState
from models.config import AudiobookConfig, TTSConfig, OutputConfig, ChapterDetectionConfig
from modules.parser.pdf_parser import PDFParser
from modules.splitter.chapter_splitter import ChapterSplitter
from modules.tts.pyttsx3_tts import Pyttsx3TTS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Input file
    book_path = Path.home() / "Téléchargements/Audiobook-Generator Test books/Autogen_and_LangGraph_Frameworks.pdf"
    output_dir = Path("./test_output_offline")

    print(f"\n{'='*60}")
    print(f"Testing Audiobook Generator (OFFLINE MODE - pyttsx3)")
    print(f"{'='*60}")
    print(f"📖 Book: {book_path.name}")
    print(f"📁 Output: {output_dir}")
    print(f"🎙️  TTS: pyttsx3 (offline)")
    print(f"{'='*60}\n")

    # Configuration
    config = AudiobookConfig(
        tts=TTSConfig(
            provider="pyttsx3",
            voice="default",
            speed=1.3,
            language="en"
        ),
        output=OutputConfig(
            format="mp3",
            bitrate="128k",
            directory=str(output_dir)
        ),
        chapter_detection=ChapterDetectionConfig(
            method="regex",
            pattern=r"^(Chapter|CHAPTER)\s+\d+"
        )
    )

    try:
        # Step 1: Parse PDF
        logger.info(f"📄 Parsing PDF: {book_path}")
        parser = PDFParser()
        book = parser.parse(book_path)
        logger.info(f"✓ Successfully parsed: {book.title}")
        logger.info(f"  Pages extracted, total text length: {len(book.raw_text)} chars")

        # Step 2: Split into chapters
        logger.info("\n📖 Splitting into chapters...")
        splitter = ChapterSplitter(config.chapter_detection)
        book = splitter.split_and_update_book(book)
        logger.info(f"✓ Found {len(book.chapters)} chapters")
        for ch in book.chapters:
            logger.info(f"  - {ch.title} ({len(ch.text)} chars)")

        # Step 3: Generate audio
        logger.info("\n🎙️  Generating audio for chapters...")
        tts = Pyttsx3TTS(
            voice=config.tts.voice,
            speed=config.tts.speed,
            language=config.tts.language
        )

        chapters_dir = output_dir / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        successful = 0
        failed = []

        for chapter in book.chapters:
            try:
                audio_filename = f"chapter_{chapter.number:02d}.{config.output.format}"
                audio_path = chapters_dir / audio_filename

                logger.info(f"  Generating Chapter {chapter.number}...")
                generated_path = tts.generate_audio(chapter, audio_path)
                chapter.audio_path = generated_path
                successful += 1
                logger.info(f"  ✓ Chapter {chapter.number} complete → {audio_filename}")

            except Exception as e:
                logger.error(f"  ✗ Chapter {chapter.number} failed: {e}")
                failed.append(chapter.number)
                continue

        # Summary
        print(f"\n{'='*60}")
        print(f"✅ Generation Complete!")
        print(f"📚 Book: {book.title}")
        print(f"📊 Success: {successful}/{len(book.chapters)} chapters")
        if failed:
            print(f"⚠️  Failed: {failed}")
        print(f"📁 Output: {output_dir}/chapters/")
        print(f"{'='*60}\n")

        # List generated files
        if successful > 0:
            print("Generated audio files:")
            for ch in book.chapters:
                if ch.audio_path:
                    file_size = Path(ch.audio_path).stat().st_size / 1024  # KB
                    print(f"  ✓ {Path(ch.audio_path).name} ({file_size:.1f} KB)")

    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
