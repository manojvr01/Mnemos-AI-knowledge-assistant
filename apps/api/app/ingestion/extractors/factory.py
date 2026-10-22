from app.ingestion.extractors.base import BaseExtractor, ExtractedDocument, ExtractedPage
from app.ingestion.extractors.pdf import PDFExtractor
from app.ingestion.extractors.docx import DocxExtractor
from app.ingestion.extractors.txt import TxtExtractor


def get_extractor(mime_type: str) -> BaseExtractor:
    """Return extractor based on verified MIME type."""
    if mime_type == "application/pdf":
        return PDFExtractor()
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return DocxExtractor()
    elif mime_type == "text/plain":
        return TxtExtractor()
    else:
        raise ValueError(f"No extractor registered for MIME type: {mime_type}")
