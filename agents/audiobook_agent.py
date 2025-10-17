import logging
from langgraph.graph import StateGraph, END
from pathlib import Path

from models.config import AudiobookConfig
from agents.audiobook_state import AudiobookState
from modules.parser.pdf_parser import PDFParser
from modules.splitter.chapter_splitter import ChapterSplitter
from modules.tts.edge_tts_provider import EdgeTTS



logger = logging.getLogger(__name__)

class AudiobookAgent:
    """LangGraph agent for audiobook generation"""
    def __init__(self, config: AudiobookConfig):
        self.config = config
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the agent workflow"""
        workflow = StateGraph(AudiobookState)

        # Add nodes
        workflow.add_node("parse", self.parse_node)
        workflow.add_node("split", self.split_node)
        workflow.add_node("tts", self.tts_node)

        # Set entry point
        workflow.set_entry_point("parse")

        # Add edges
        workflow.add_conditional_edges(
            "parse",
            self.route_after_step,
            {
                "continue": "split",
                "end": END
            })
        
        workflow.add_conditional_edges(
            "split",
            self.route_after_step,
            {
                "continue": "tts",
                "end": END
            })
        

        return workflow.compile()
    
    def parse_node(self, state: AudiobookState) -> AudiobookState:
        """Parse PDF and extract text"""
        try:
            logger.info(f"Parsing book : {state['book_path']}")
            parser = PDFParser()
            book  = parser.parse(Path(state['book_path']))

            # check if there is extracted content
            if not book.raw_text or len(book.raw_text.strip()) == 0:
                return {
                    **state,
                    "error": "fatal: File contains no data to extract"
                }

            logger.info(f"Successfully parsed : {book.title}")

            return {
                **state,
                "book": book,
                "error": None
            }

        except FileNotFoundError as e:
            return {
                **state,
                "error": f"fatal: File not found - {e}"
            }
        except Exception as e:
            return {
                **state,
                "error": f"fatal: Failed to parse PDF - {e}"
            }
        
    def split_node(self, state: AudiobookState) -> AudiobookState:
        """Split book into chapters"""
        try:
            logger.info("Splitting book into chapters")
            splitter = ChapterSplitter(self.config.chapter_detection)
            book = splitter.split_and_update_book(state['book'])

            logger.info(f"Found {len(book.chapters)} chapters")
            return {
                **state,
                "book": book,
                "error": None
            }
        except Exception as e:
            return {
                **state,
                "error": f"fatal: Failed to split chapters - {e}"
            }
        
    def tts_node(self, state: AudiobookState) -> AudiobookState:
        """Generate audio for each chapter"""
        try:
            logger.info("Generating audio for chapters")
            tts = EdgeTTS(
                voice=self.config.tts.voice,
                speed=self.config.tts.speed,
                language=self.config.tts.language
            )

            book = state['book']
            output_dir = Path(state['output_dir'])
            chapters_dir = output_dir / "chapters"
            chapters_dir.mkdir(parents=True, exist_ok=True)

            successful_chapters = 0
            failed_chapters = []

            for chapter in book.chapters:
                try:
                    # Generate audio filename
                    audio_filename = f"chapter_{chapter.number:02d}.{self.config.output.format}"
                    audio_path = chapters_dir / audio_filename

                    # Generate audio
                    generated_path = tts.generate_audio(chapter, audio_path)
                    chapter.audio_path = generated_path
                    successful_chapters += 1

                    logger.info(f"✓ Chapter {chapter.number} complete")

                except Exception as e:
                    # Non-fatal: log and continue with next chapter
                    logger.warning(f"✗ Chapter {chapter.number} failed: {e}")
                    failed_chapters.append(chapter.number)
                    continue
            
            # Fatal error: ALL chapters failed
            if successful_chapters == 0:
                return {
                    **state,
                    "error": "fatal: All chapters failed to generate audio"
                }
            
            # Partial failure: some chapters succeeded
            if failed_chapters:
                warning_msg = f"warning: {len(failed_chapters)} chapters failed: {failed_chapters}"
                logger.warning(warning_msg)
                # Remove failed chapters from book
                book.chapters = [ch for ch in book.chapters if ch.audio_path]

            logger.info(f"Audio generation complete: {successful_chapters}/{len(book.chapters)} chapters")
            return {
                **state,
                "book": book,
                "error": None
            }

        except Exception as e:
            return {
                **state,
                "error": f"fatal: TTS initialization failed - {e}"
            }
        
    def route_after_step(self, state: AudiobookState) -> str:
        """Conditional routing: stop on fatal errors, continue otherwise"""
        error = state.get("error")

        if error and error.startswith("fatal"):
            logger.error(f"Fatal error encountered: {error}")
            return "end"
        
        return "continue"