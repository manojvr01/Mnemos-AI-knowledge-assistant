import uuid
import logging
from sqlalchemy import select, delete
from app.db.session import get_session_maker
from app.models.document import Document, DocumentChunk
from app.models.ingestion_job import IngestionJob
from app.storage import get_storage
from app.ingestion.extractors.factory import get_extractor
from app.ingestion.chunker import RecursiveCharacterChunker
from app.embeddings.factory import get_embedding_provider
from app.core.config import settings

logger = logging.getLogger(__name__)


async def process_document_ingestion(
    document_id: uuid.UUID,
    storage_key: str,
    mime_type: str,
    session_factory=None,
) -> None:
    """
    Background worker task to extract text, chunk, embed, and index an uploaded document.
    Ensures safe error recording and clean rollback on any failure.
    """
    storage = get_storage()
    chunker = RecursiveCharacterChunker()
    maker = session_factory or get_session_maker()

    async with maker() as db:
        # Load document & ingestion job
        doc_stmt = select(Document).where(Document.id == document_id)
        doc = (await db.execute(doc_stmt)).scalar_one_or_none()

        job_stmt = select(IngestionJob).where(IngestionJob.document_id == document_id)
        job = (await db.execute(job_stmt)).scalar_one_or_none()

        if not doc:
            logger.error(f"Ingestion aborted: Document {document_id} not found.")
            return

        try:
            # 1. Update status to PROCESSING / PARSING
            doc.status = "PROCESSING"
            if job:
                job.status = "PROCESSING"
                job.stage = "PARSING"
            await db.commit()

            # 2. Read bytes from storage
            content = await storage.read_file(storage_key)

            # 3. Extract text
            extractor = get_extractor(mime_type)
            extracted = extractor.extract(content)

            doc.page_count = extracted.page_count
            if job:
                job.stage = "CHUNKING"
            await db.commit()

            # 4. Chunk text
            chunks = chunker.chunk_pages(extracted.pages)
            if not chunks:
                raise ValueError("No readable text chunks could be produced from this document.")

            if job:
                job.stage = "EMBEDDING"
            await db.commit()

            # 5. Generate embeddings
            embedding_provider = get_embedding_provider()
            chunk_texts = [c.content for c in chunks]
            vectors = await embedding_provider.embed_texts(chunk_texts)

            # Clean any existing chunks for safety
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))

            for c, vec in zip(chunks, vectors):
                doc_chunk = DocumentChunk(
                    document_id=doc.id,
                    workspace_id=doc.workspace_id,
                    chunk_index=c.index,
                    content=c.content,
                    page_number=c.page_number,
                    start_char_offset=c.start_char_offset,
                    end_char_offset=c.end_char_offset,
                    token_count=c.token_count,
                    embedding=vec,
                    embedding_model=embedding_provider.model_name,
                    embedding_version="v1",
                )
                db.add(doc_chunk)

            # 6. Complete
            doc.status = "INDEXED"
            doc.error_message = None
            if job:
                job.status = "COMPLETED"
                job.stage = "INDEXED"

            await db.commit()
            logger.info(f"Document {document_id} successfully indexed ({len(chunks)} chunks).")

        except Exception as e:
            await db.rollback()
            # Clean chunks if any were added
            try:
                await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            except Exception:
                pass

            error_msg = str(e)
            logger.warning(f"Ingestion failed for document {document_id}: {error_msg}")

            # Re-fetch doc to set safe failure state
            fail_doc_stmt = select(Document).where(Document.id == document_id)
            failed_doc = (await db.execute(fail_doc_stmt)).scalar_one_or_none()
            if failed_doc:
                failed_doc.status = "FAILED"
                failed_doc.error_message = error_msg[:500]

            fail_job_stmt = select(IngestionJob).where(IngestionJob.document_id == document_id)
            failed_job = (await db.execute(fail_job_stmt)).scalar_one_or_none()
            if failed_job:
                failed_job.status = "FAILED"
                failed_job.safe_error = error_msg[:500]

            await db.commit()
