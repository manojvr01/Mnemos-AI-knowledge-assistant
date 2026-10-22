from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ExtractedPage:
    page_number: int | None # 1-indexed for PDFs; None for DOCX/TXT
    text: str


@dataclass
class ExtractedDocument:
    pages: list[ExtractedPage]
    page_count: int | None
    total_characters: int


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, content: bytes) -> ExtractedDocument:
        """Extract text from raw document bytes, preserving page boundaries when possible."""
        pass
