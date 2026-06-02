# documents.py handles all HTTP routing for document ingestion.
# Accepts file uploads, validates type, saves to temp storage,
# and delegates to document_service for the full pipeline.
#
# FastAPI's UploadFile handles multipart form uploads —
# the standard format for file uploads over HTTP.

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

router = APIRouter(prefix="/documents", tags=["Documents"])

# Supported file types — extend this list to add new formats
ALLOWED_TYPES = {"pdf", "docx"}

# Max file size — 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/", response_model=DocumentUploadResponse, status_code=201)
@limiter.limit("20/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    institution_id: str = "default"
):
    """
    Accepts a PDF or DOCX file upload and runs the full
    ingestion pipeline — extract, chunk, embed, store in Pinecone.

    The response includes a document_id the client can use
    to reference this document in future RAG-powered goals.

    Args:
        file: The uploaded file (multipart form data)
        institution_id: Which institution owns this document
                       Defaults to 'default' for pilot

    Returns:
        DocumentUploadResponse with document_id and chunk count
    """
    # Validate file type
    filename = file.filename or "unknown"
    file_extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if file_extension not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{file_extension}'. "
                   f"HERVEX accepts PDF and DOCX files only."
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is 10MB. "
                   f"Received: {len(content) / 1024 / 1024:.1f}MB"
        )

    # Save to temp uploads directory
    # Processor reads from disk — needs a file path
    os.makedirs("uploads", exist_ok=True)
    temp_filename = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join("uploads", temp_filename)

    with open(temp_path, "wb") as f:
        f.write(content)

    logger.info(
        f"[{APP_NAME}] Documents: Received {filename} "
        f"({len(content) / 1024:.1f}KB) — starting ingestion"
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


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """
    Returns the current ingestion status of a document.
    Use this to check if a document has finished indexing
    before submitting goals that reference it.

    Args:
        document_id: The ID returned from the upload endpoint
    """
    doc = await get_document_by_id(document_id)

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {document_id}"
        )

    return DocumentStatusResponse(**doc)


@router.get("/", response_model=DocumentListResponse)
async def list_documents(institution_id: str = "default"):
    """
    Lists all documents indexed for a given institution.
    Shows filename, status, chunk count, and indexing date.

    Args:
        institution_id: Filter by institution
    """
    docs = await get_all_documents(institution_id)
    return DocumentListResponse(
        documents=docs,
        total=len(docs),
        institution_id=institution_id
    )


@router.delete("/{document_id}", status_code=200)
async def delete_document_endpoint(document_id: str):
    """
    Removes a document from both Pinecone and MongoDB.
    All vectors associated with this document are deleted.
    This action cannot be undone.

    Args:
        document_id: The ID of the document to remove
    """
    doc = await get_document_by_id(document_id)

    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document not found: {document_id}"
        )

    await remove_document(document_id)

    return {
        "message": f"Document {document_id} successfully removed "
                   f"from HERVEX knowledge base",
        "document_id": document_id
    }
