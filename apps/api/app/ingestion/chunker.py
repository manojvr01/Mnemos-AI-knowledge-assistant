from dataclasses import dataclass
from typing import List
from app.ingestion.extractors.base import ExtractedPage


@dataclass
class Chunk:
    index: int
    content: str
    page_number: int | None
    start_char_offset: int
    end_char_offset: int
    token_count: int


class RecursiveCharacterChunker:
    def __init__(
        self,
        chunk_size: int = 500, # Approximate tokens (~2000 chars)
        chunk_overlap: int = 50, # Approximate tokens (~200 chars)
        separators: List[str] | None = None,
    ):
        self.chunk_size_chars = chunk_size * 4 # 1 token ≈ 4 chars
        self.chunk_overlap_chars = chunk_overlap * 4
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def chunk_pages(self, pages: List[ExtractedPage]) -> List[Chunk]:
        """Split extracted pages into bounded, overlapping chunks with page metadata."""
        all_chunks: List[Chunk] = []
        global_index = 0

        for page in pages:
            text = page.text
            if not text:
                continue

            page_chunks = self._chunk_text(text, page.page_number, global_index)
            all_chunks.extend(page_chunks)
            global_index += len(page_chunks)

        return all_chunks

    def _chunk_text(self, text: str, page_number: int | None, starting_index: int) -> List[Chunk]:
        chunks: List[Chunk] = []
        text_len = len(text)
        if text_len == 0:
            return chunks

        # If text is smaller than chunk size, return single chunk
        if text_len <= self.chunk_size_chars:
            token_est = max(1, len(text) // 4)
            return [
                Chunk(
                    index=starting_index,
                    content=text,
                    page_number=page_number,
                    start_char_offset=0,
                    end_char_offset=text_len,
                    token_count=token_est,
                )
            ]

        start = 0
        idx = starting_index

        while start < text_len:
            end = start + self.chunk_size_chars
            if end >= text_len:
                chunk_str = text[start:text_len].strip()
                if chunk_str:
                    chunks.append(
                        Chunk(
                            index=idx,
                            content=chunk_str,
                            page_number=page_number,
                            start_char_offset=start,
                            end_char_offset=text_len,
                            token_count=max(1, len(chunk_str) // 4),
                        )
                    )
                break

            # Find best split point using separators
            split_point = -1
            sub = text[start:end]

            for sep in self.separators:
                if not sep:
                    split_point = end
                    break
                r_idx = sub.rfind(sep)
                if r_idx != -1 and r_idx > (self.chunk_size_chars // 3):
                    split_point = start + r_idx + len(sep)
                    break

            if split_point == -1 or split_point <= start:
                split_point = end

            chunk_str = text[start:split_point].strip()
            if chunk_str:
                chunks.append(
                    Chunk(
                        index=idx,
                        content=chunk_str,
                        page_number=page_number,
                        start_char_offset=start,
                        end_char_offset=split_point,
                        token_count=max(1, len(chunk_str) // 4),
                    )
                )
                idx += 1

            # Advance with overlap
            start = max(start + 1, split_point - self.chunk_overlap_chars)

        return chunks
