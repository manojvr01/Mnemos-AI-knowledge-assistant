from app.ingestion.extractors.base import BaseExtractor, ExtractedDocument, ExtractedPage


class TxtExtractor(BaseExtractor):
    def extract(self, content: bytes) -> ExtractedDocument:
        try:
            text = content.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1").strip()
            except Exception as e:
                raise ValueError(f"Unable to decode text document: {str(e)}") from e

        if not text:
            raise ValueError("Text document is empty.")

        page = ExtractedPage(page_number=None, text=text)
        return ExtractedDocument(
            pages=[page],
            page_count=None,
            total_characters=len(text)
        )
