pp = typer.Typer(help="Convert PDF books to audiobooks using AI", invoke_without_command=True)
console = Console()


@app.callback()
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
        1.0,
        "--speed", "-s",
        help="Speech speed (0.5 - 2.0)"
    ),
    chapter_pattern: str = typer.Option(
        r"^Chapter \d+",
        "--pattern", "-p",
        help="Regex pattern for chapter detection"
    )
):
    """
    Generate an audiobook from a PDF file

    Example:
        audiobook-gen mybook.pdf -o ./my_audiobook -f mp3
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
    console.print(Panel.fit(
        f"[bold cyan]Audiobook Generator[/bold cyan]\n\n"
        f"📖 Book: [yellow]{pdf_file.name}[/yellow]\n"
        f"📁 Output: [yellow]{output_path}[/yellow]\n"
        f"🎵 Format: [yellow]{format}[/yellow]\n"
        f"🗣️  Voice: [yellow]{voice}[/yellow]\n"
        f"⚡ Speed: [yellow]{speed}x[/yellow]",
        title="Configuration"
    ))



@app.command()
def version():
    """Show version information"""
    console.print("[bold cyan]Audiobook Generator[/bold cyan] v0.1.0")
    console.print("Powered by LangGraph + Coqui TTS")


if __name__ == "__main__":
    app()
