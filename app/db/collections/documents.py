# documents.py contains all MongoDB operations for the
# ingested_documents collection.
# Tracks every document uploaded to HERVEX Education
# and its ingestion status through the pipeline.

from datetime import datetime, timezone
from typing import Optional, List
from app.db.connection import get_database
from app.enums.status import DocumentStatus
from loguru import logger
from app.core.settings import APP_NAME

async def insert_document(document: dict) -> str:
    """
    Inserts a new document record into the
    ingested_documents collection.

    Args:
        document: Dictionary built by IngestedDocument.create()

    Returns:
        The document_id of the inserted record
    """
    db = get_database()
    await db.ingested_documents.insert_one(document)
    logger.info(
        f"[{APP_NAME}] DB: Inserted document record "
        f"{document['document_id']}"
    )
    return document["document_id"]

async def get_document_by_id(document_id: str) -> Optional[dict]:
    """
    Retrieves a document record by its unique ID.

    Args:
        document_id: The document's unique identifier

    Returns:
        The document dictionary or None if not found
    """
    db = get_database()
    return await db.ingested_documents.find_one(
        {"document_id": document_id}
    )

async def get_all_documents(institution_id: str = "default") -> List[dict]:
    """
    Retrieves all documents for a given institution.
    Used by the document listing endpoint.

    Args:
        institution_id: Filter by institution

    Returns:
        List of document dictionaries
    """
    db = get_database()
    cursor = db.ingested_documents.find(
        {"institution_id": institution_id}
    )
    return await cursor.to_list(length=100)

async def update_document_status(
    document_id: str,
    status: DocumentStatus,
    chunk_count: int = None,
    char_count: int = None,
    error: str = None
):
    """
    Updates a document's ingestion status and optional
    metrics after each pipeline stage completes.

    Args:
        document_id: The document's unique identifier
        status: New DocumentStatus value
        chunk_count: Number of chunks stored in Pinecone
        char_count: Total characters extracted from document
        error: Error message if ingestion failed
    """
    db = get_database()

    update_fields = {
        "status": status,
        "updated_at": datetime.utcnow()
    }

    if chunk_count is not None:
        update_fields["chunk_count"] = chunk_count
    if char_count is not None:
        update_fields["char_count"] = char_count
    if error is not None:
        update_fields["error"] = error
    if status == DocumentStatus.INDEXED:
        update_fields["indexed_at"] = datetime.now(timezone.utc).isoformat()

    await db.ingested_documents.update_one(
        {"document_id": document_id},
        {"$set": update_fields}
    )
    logger.info(
        f"[{APP_NAME}] DB: Updated document {document_id} "
        f"status → {status}"
    )

async def delete_document(document_id: str) -> bool:
    """
    Removes a document record from MongoDB.
    Called alongside Pinecone vector deletion when
    a document is removed from the system.

    Args:
        document_id: The document's unique identifier

    Returns:
        True if deletion was successful
    """
    db = get_database()
    result = await db.ingested_documents.delete_one(
        {"document_id": document_id}
    )
    return result.deleted_count > 0
