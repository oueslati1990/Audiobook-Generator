import logging
from langgraph.graph import StateGraph, END
from pathlib import Path

from models.config import AudiobookConfig
from agents.audiobook_state import AudiobookState
from modules.parser.pdf_parser import PDFParser
from modules.splitter.chapter_splitter import ChapterSplitter



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
        

        return workflow.compile()
    
    def parse_node(self, state: AudiobookState) -> AudiobookState:
        """Parse PDF and extract text"""
        try:
            logger.info(f"Parsing book : {state['book_path']}")
            parser = PDFParser()
            book  = parser.parse(Path(state['book']))

            # check if there is extracted content
            if not book.raw_text or len(book.raw_text.strip() == 0):
                return {
                    **state,
                    "error": "File contains no data to extract"
                }
            
            logger.info(f"Sucessfully parsed : {book.title}")

            return {
                **state,
                "Book": book,
                "error": None
            }

        except FileNotFoundError as e:
            return {
                **state,
                "error": f"Fatal : file not found - {e}"
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
                "error": f"Failed to split chapters - {e}"
            }
        
    def route_after_step(self, state: AudiobookState) -> str:
        """Conditional routing: stop on fatal errors, continue otherwise"""
        error = state.get("error")

        if error and error.startswith("fatal"):
            logger.error(f"Fatal error encountered: {error}")
            return "end"
        
        return "continue"