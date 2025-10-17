"""CLI interface for audiobook generator"""

import typer
import logging
from typing import Optional
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler

from models.config import AudiobookConfig, TTSConfig, OutputConfig, ChapterDetectionConfig
from agents.audiobook_agent import AudiobookAgent

# Setup rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

app = typer.Typer(help="Convert PDF books to audiobooks using AI")
console = Console()


@app.command()
def generate(
    pdf_path: str = typer.Argument(..., help="Path to PDF book file"),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir", "-o",
        help="Output directory (default: ./audiobooks/<book_name>)"
    ),
    voice: str = typer.Option(
        "default",
        "--voice", "-v",
        help="TTS voice to use"
    ),
    format: str = typer.Option(
        "mp3",
        "--format", "-f",
        help="Audio format (mp3, wav, ogg, flac)"
    ),
    speed: float = typer.Option(
        1.3,
        "--speed", "-s",
        help="Speech speed (0.5 - 2.0)"
    ),
    chapter_pattern: str = typer.Option(
        r"^(Chapter|CHAPTER)\s+\d+",
        "--pattern", "-p",
        help="Regex pattern for chapter detection"
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Use offline TTS (pyttsx3) instead of Edge TTS"
    )
):
    """
    Generate an audiobook from a PDF file

    Example:
        python -m cli.main generate mybook.pdf -o ./my_audiobook -f mp3
        python -m cli.main generate mybook.pdf --offline
    """

    # Validate PDF path
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        console.print(f"[red]✗ Error: File not found: {pdf_path}[/red]")
        raise typer.Exit(1)

    if pdf_file.suffix.lower() != '.pdf':
        console.print(f"[red]✗ Error: File must be a PDF, got: {pdf_file.suffix}[/red]")
        raise typer.Exit(1)

    # Determine output directory
    if output_dir is None:
        output_dir = f"./audiobooks/{pdf_file.stem}"

    output_path = Path(output_dir)

    # Show configuration
    tts_mode = "pyttsx3 (offline)" if offline else "Edge TTS (online)"
    console.print(Panel.fit(
        f"[bold cyan]Audiobook Generator[/bold cyan]\n\n"
        f"📖 Book: [yellow]{pdf_file.name}[/yellow]\n"
        f"📁 Output: [yellow]{output_path}[/yellow]\n"
        f"🎵 Format: [yellow]{format}[/yellow]\n"
        f"🎙️  TTS: [yellow]{tts_mode}[/yellow]\n"
        f"🗣️  Voice: [yellow]{voice}[/yellow]\n"
        f"⚡ Speed: [yellow]{speed}x[/yellow]",
        title="Configuration"
    ))

    # Build configuration
    config = AudiobookConfig(
        tts=TTSConfig(
            provider="pyttsx3" if offline else "edge-tts",
            voice=voice,
            speed=speed,
            language="en"
        ),
        output=OutputConfig(
            format=format,
            bitrate="128k",
            directory=output_dir
        ),
        chapter_detection=ChapterDetectionConfig(
            method="regex",
            pattern=chapter_pattern
        )
    )

    # Create agent with appropriate TTS
    if offline:
        # Import and temporarily replace the TTS class before creating agent
        from modules.tts.pyttsx3_tts import Pyttsx3TTS
        import sys
        import agents.audiobook_agent as agent_module

        # Store original
        original_import = agent_module.EdgeTTS
        # Replace with offline TTS
        agent_module.EdgeTTS = Pyttsx3TTS

        agent = AudiobookAgent(config)

        # Restore original (not strictly necessary but clean)
        agent_module.EdgeTTS = original_import
    else:
        agent = AudiobookAgent(config)

    # Create initial state
    initial_state = {
        "book_path": str(pdf_file),
        "book": None,
        "config": config,
        "output_dir": str(output_path),
        "error": None
    }

    # Run workflow
    console.print("\n[bold cyan]🚀 Starting audiobook generation...[/bold cyan]\n")

    try:
        result = agent.workflow.invoke(initial_state)

        console.print()
        if result.get("error"):
            console.print(f"[bold red]❌ Generation failed:[/bold red] {result['error']}")
            raise typer.Exit(1)
        else:
            book = result.get("book")
            if book and book.chapters:
                console.print(Panel.fit(
                    f"[bold green]✅ Success![/bold green]\n\n"
                    f"📚 Book: [yellow]{book.title}[/yellow]\n"
                    f"📖 Chapters: [yellow]{len(book.chapters)}[/yellow]\n"
                    f"📁 Location: [yellow]{output_path}/chapters/[/yellow]",
                    title="Generation Complete",
                    border_style="green"
                ))

                console.print("\n[bold]Generated Files:[/bold]")
                for chapter in book.chapters:
                    if chapter.audio_path:
                        file_path = Path(chapter.audio_path)
                        size = file_path.stat().st_size / (1024 * 1024)  # MB
                        console.print(f"  ✓ {file_path.name} ([cyan]{size:.2f} MB[/cyan])")
            else:
                console.print("[yellow]⚠️  No chapters were generated[/yellow]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)




@app.command()
def version():
    """Show version information"""
    console.print("[bold cyan]Audiobook Generator[/bold cyan] v0.1.0")
    console.print("Powered by LangGraph + Edge TTS / pyttsx3")


@app.command()
def list_voices():
    """List available TTS voices"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        console.print("\n[bold cyan]Available Voices (pyttsx3 - offline):[/bold cyan]\n")
        for i, voice in enumerate(voices, 1):
            console.print(f"  {i}. [yellow]{voice.name}[/yellow]")
            console.print(f"     ID: [dim]{voice.id}[/dim]")
            console.print(f"     Languages: [dim]{voice.languages}[/dim]\n")

    except Exception as e:
        console.print(f"[red]Error listing voices: {e}[/red]")


if __name__ == "__main__":
    app()
