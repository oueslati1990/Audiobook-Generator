#!/usr/bin/env python3
"""Test script for audiobook generation using offline TTS (pyttsx3)"""

import logging
from pathlib import Path

from agents.audiobook_agent import AudiobookAgent
from models.config import AudiobookConfig, TTSConfig, OutputConfig, ChapterDetectionConfig

# Temporarily patch the import to use pyttsx3
import sys
from modules.tts.pyttsx3_tts import Pyttsx3TTS
sys.modules['modules.tts.edge_tts_provider'].EdgeTTS = Pyttsx3TTS

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    # Input file
    book_path = Path.home() / "Téléchargements/Audiobook-Generator Test books/Autogen_and_LangGraph_Frameworks.pdf"
    output_dir = Path("./test_output_offline")

    print(f"\n{'='*60}")
    print(f"Testing Audiobook Generator (OFFLINE MODE)")
    print(f"{'='*60}")
    print(f"📖 Book: {book_path}")
    print(f"📁 Output: {output_dir}")
    print(f"🎙️  TTS: pyttsx3 (offline)")
    print(f"{'='*60}\n")

    # Create configuration
    config = AudiobookConfig(
        tts=TTSConfig(
            provider="pyttsx3",
            voice="default",
            speed=1.3,  # Slightly faster
            language="en"
        ),
        output=OutputConfig(
            format="mp3",
            bitrate="128k",
            directory=str(output_dir)
        ),
        chapter_detection=ChapterDetectionConfig(
            method="regex",
            pattern=r"^(Chapter|CHAPTER)\s+\d+"  # Match "Chapter 1", "CHAPTER 1", etc.
        )
    )

    # Create agent
    agent = AudiobookAgent(config)

    # Create initial state
    initial_state = {
        "book_path": str(book_path),
        "book": None,
        "config": config,
        "output_dir": str(output_dir),
        "error": None
    }

    print("🚀 Starting audiobook generation...\n")

    # Run the workflow
    try:
        result = agent.workflow.invoke(initial_state)

        print(f"\n{'='*60}")
        if result.get("error"):
            print(f"❌ Generation failed: {result['error']}")
        else:
            book = result.get("book")
            if book:
                print(f"✅ Generation complete!")
                print(f"📚 Book: {book.title}")
                print(f"📖 Chapters generated: {len(book.chapters)}")
                print(f"\nChapter details:")
                for chapter in book.chapters:
                    audio_status = "✓" if chapter.audio_path else "✗"
                    print(f"  {audio_status} Chapter {chapter.number}: {chapter.title}")
                    if chapter.audio_path:
                        print(f"      → {chapter.audio_path}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
