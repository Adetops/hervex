# v1/documents.py — versioned document ingestion endpoints
# POST /v1/institution/{institution_id}/documents
# The institution_id is now a path parameter — not a query param.
# This makes institution ownership explicit in the URL structure.

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from loguru import logger
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentListResponse
)
from app.services.document_service import ingest_document, remove_document
from app.db.collections.documents import get_document_by_id, get_all_documents
from app.core.settings import APP_NAME
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/v1", tags=["Documents"])

ALLOWED_TYPES = {"pdf", "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@router.post(
    "/institution/{institution_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=201
)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    institution_id: str,
    file: UploadFile = File(...)
):
    """
    Upload a curriculum document to an institution's knowledge base.

    Accepts PDF and DOCX files up to 10MB.
    HERVEX will extract text, split into chunks, convert to
    vector embeddings, and store in the institution's isolated
    Pinecone namespace.

    Once indexed, HERVEX can search this document when students
    and lecturers submit goals for that institution.

    Returns a document_id — use this to track ingestion status
    or restrict RAG searches to this specific document.
    """
    filename = file.filename or "unknown"
    file_extension = (
        filename.rsplit(".", 1)[-1].lower()
        if "." in filename else ""
    )

    if file_extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: '{file_extension}'. "
                f"HERVEX accepts PDF and DOCX files only."
            )
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File too large. Maximum size is 10MB. "
                f"Received: {len(content) / 1024 / 1024:.1f}MB"
            )
        )

    os.makedirs("uploads", exist_ok=True)
    temp_filename = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join("uploads", temp_filename)

    with open(temp_path, "wb") as f:
        f.write(content)

    logger.info(
        f"[{APP_NAME}] POST /v1/institution/{institution_id}/documents "
        f"— {filename} ({len(content) / 1024:.1f}KB)"
    )

    try:
        result = await ingest_document(
            file_path=temp_path,
            filename=filename,
            file_type=file_extension,
            institution_id=institution_id
        )
        return DocumentUploadResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {str(e)}"
        )


@router.get(
    "/institution/{institution_id}/documents",
    response_model=DocumentListResponse
)
async def list_documents(institution_id: str):
    """
    List all documents indexed for an institution.
    Shows filename, status, chunk count, and indexing date.
    """
    docs = await get_all_documents(institution_id)
    return DocumentListResponse(
        documents=docs,
        total=len(docs),
        institution_id=institution_id
    )


@router.get(
    "/institution/{institution_id}/documents/{document_id}",
    response_model=DocumentStatusResponse
)
async def get_document_status(institution_id: str, document_id: str):
    """
    Check the ingestion status of a specific document.
    Use this to confirm a document is fully indexed before
    submitting goals that reference it.
    """
    doc = await get_document_by_id(document_id)

    if not doc or doc.get("institution_id") != institution_id:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {document_id}"
        )

    return DocumentStatusResponse(**doc)


@router.delete(
    "/institution/{institution_id}/documents/{document_id}",
    status_code=200
)
async def delete_document(institution_id: str, document_id: str):
    """
    Remove a document from the institution's knowledge base.
    Deletes all vectors from Pinecone and the metadata from MongoDB.
    This action cannot be undone.
    """
    doc = await get_document_by_id(document_id)

    if not doc or doc.get("institution_id") != institution_id:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {document_id}"
        )

    await remove_document(document_id)

    return {
        "message": (
            f"Document {document_id} successfully removed "
            f"from institution '{institution_id}' knowledge base"
        ),
        "document_id": document_id
    }
