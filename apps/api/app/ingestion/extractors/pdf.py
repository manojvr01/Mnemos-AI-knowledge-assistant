import io
from pypdf import PdfReader
from app.ingestion.extractors.base import BaseExtractor, ExtractedDocument, ExtractedPage


class PDFExtractor(BaseExtractor):
    def extract(self, content: bytes) -> ExtractedDocument:
        try:
            stream = io.BytesIO(content)
            reader = PdfReader(stream)
        except Exception as e:
            raise ValueError(f"Unable to parse PDF stream: {str(e)}") from e

        if reader.is_encrypted:
            raise ValueError("PDF is password-protected or encrypted.")

        page_count = len(reader.pages)
        if page_count == 0:
            raise ValueError("PDF document contains 0 pages.")

        extracted_pages: list[ExtractedPage] = []
        total_chars = 0

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1 # 1-indexed
            text = (page.extract_text() or "").strip()
            extracted_pages.append(ExtractedPage(page_number=page_num, text=text))
            total_chars += len(text)

        # Check if the PDF has selectable text
        if total_chars == 0:
            raise ValueError("PDF contains no extractable text. Scanned or image-only documents require OCR (not supported in MVP).")

        return ExtractedDocument(
            pages=extracted_pages,
            page_count=page_count,
            total_characters=total_chars
        )
