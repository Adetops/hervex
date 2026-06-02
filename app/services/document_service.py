# document_service.py orchestrates the full document ingestion pipeline.
# It is the only place that coordinates processor → chunker → embedder
# → Pinecone in the correct order.
#
# Flow:
# 1. Create MongoDB record with UPLOADED status
# 2. Extract text from file (processor)
# 3. Split into chunks (chunker)
# 4. Convert to embeddings (embedder)
# 5. Store in Pinecone (pinecone_client)
# 6. Update MongoDB record with INDEXED status and metrics
# 7. Clean up temp file
#
# Any failure at any stage is caught, the document status
# is updated to FAILED, and the error is logged.

import os
import uuid
from loguru import logger
from app.core.settings import APP_NAME
from app.ingestion.processor import extract_text
from app.ingestion.chunker import chunk_text
from app.ingestion.embedder import embed_chunks
from app.vectorstore.pinecone_client import upsert_chunks, delete_document_chunks
from app.db.documents.ingested_document import IngestedDocument
from app.db.collections.documents import (
    insert_document,
    update_document_status,
    delete_document
)
from app.enums.status import DocumentStatus

async def ingest_document(
    file_path: str,
    filename: str,
    file_type: str,
    institution_id: str = "default"
) -> dict:
    """
    Runs the full ingestion pipeline for an uploaded document.
    Returns a summary of the ingestion result.

    Args:
        file_path: Temporary path where the uploaded file is stored
        filename: Original filename from the upload
        file_type: 'pdf' or 'docx'
        institution_id: Institution this document belongs to

    Returns:
        Dictionary with document_id, status, chunk_count, char_count

    Raises:
        Exception: Caught internally — status updated to FAILED
    """

    # Generate unique document ID
    document_id = str(uuid.uuid4())

    # Create initial MongoDB record
    doc_record = IngestedDocument.create(
        document_id=document_id,
        filename=filename,
        file_type=file_type,
        institution_id=institution_id
    )
    await insert_document(doc_record)

    logger.info(
        f"[{APP_NAME}] Document Service: Starting ingestion "
        f"for {filename} — ID: {document_id}"
    )

    try:
        # Stage 1 — Extract text
        await update_document_status(document_id, DocumentStatus.PROCESSING)
        raw_text = extract_text(file_path, file_type)
        char_count = len(raw_text)
        logger.info(
            f"[{APP_NAME}] Document Service: Extracted "
            f"{char_count} characters"
        )

        # Stage 2 — Chunk text
        chunks = chunk_text(raw_text, document_id)
        logger.info(
            f"[{APP_NAME}] Document Service: Created "
            f"{len(chunks)} chunks"
        )

        # Stage 3 — Embed chunks
        embedded_chunks = embed_chunks(chunks)
        logger.info(
            f"[{APP_NAME}] Document Service: Embedded "
            f"{len(embedded_chunks)} chunks"
        )

        # Stage 4 — Store in Pinecone
        total_upserted = await upsert_chunks(embedded_chunks)

        # Stage 5 — Update MongoDB with success
        await update_document_status(
            document_id,
            DocumentStatus.INDEXED,
            chunk_count=total_upserted,
            char_count=char_count
        )

        logger.info(
            f"[{APP_NAME}] Document Service: Ingestion complete "
            f"for {filename} — {total_upserted} chunks indexed"
        )

        return {
            "document_id": document_id,
            "filename": filename,
            "status": DocumentStatus.INDEXED,
            "chunk_count": total_upserted,
            "char_count": char_count,
            "message": f"Successfully indexed {total_upserted} chunks from {filename}"
        }

    except Exception as e:
        # Any failure — update status and log
        error_message = str(e)
        logger.error(
            f"[{APP_NAME}] Document Service: Ingestion failed "
            f"for {filename} — {error_message}"
        )
        await update_document_status(
            document_id,
            DocumentStatus.FAILED,
            error=error_message
        )
        raise

    finally:
        # Always clean up the temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(
                f"[{APP_NAME}] Document Service: Cleaned up "
                f"temp file {file_path}"
            )


async def remove_document(document_id: str) -> bool:
    """
    Removes a document completely from both
    Pinecone and MongoDB.

    Args:
        document_id: The document's unique identifier

    Returns:
        True if removal was successful
    """
    logger.info(
        f"[{APP_NAME}] Document Service: Removing "
        f"document {document_id}"
    )

    # Remove vectors from Pinecone first
    await delete_document_chunks(document_id)

    # Remove record from MongoDB
    await delete_document(document_id)

    logger.info(
        f"[{APP_NAME}] Document Service: Successfully removed "
        f"document {document_id}"
    )
    return True
