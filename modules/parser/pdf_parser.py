"""PDF parser implementation"""
from modules.parser.base_parser import BaseParser
from models.book import Book

from PyPDF2 import PdfReader
from pathlib import Path

class PDFParser(BaseParser):
    """Parser for PDF files"""

    def parse(self, file_path: Path) -> Book:
        """
        Parse a PDF file and extract text content

        Args:
            file_path: Path to the PDF file

        Returns:
            Book object with extracted content
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found for path : {file_path}")
        
        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected PDF file, got {file_path.suffix}")
        
        # Read PDF
        reader = PdfReader(str(file_path))

        # Extract metadata
        metadata = reader.metadata
        title = metadata.get('/Title') if metadata else None
        author = metadata.get('/Author') if metadata else None

        # Fallback to filename if no title in metadata
        if not title:
            title = self._extract_title_from_path(file_path)

        # Extract raw text
        raw_text = ""
        for page in reader.pages:
            raw_text += page.extract_text() + "\n"
        
        # Create book 
        book =  Book(
            title= title,
            author= author,
            file_path= file_path,
            raw_text= raw_text.strip()
        )

        return book