# document.py defines Pydantic schemas for document-related
# API requests and responses.
# Separate from the MongoDB document shape in db/documents/
# — these are what the API exposes to the client.

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.enums.status import DocumentStatus

class DocumentUploadResponse(BaseModel):
    """
    Returned after a successful document upload and ingestion.
    Gives the client everything needed to reference the document
    in future RAG-powered goal submissions.
    """
    document_id: str
    filename: str
    status: DocumentStatus
    chunk_count: int
    char_count: int
    message: str

class DocumentStatusResponse(BaseModel):
    """
    Returned when the client checks on a document's status.
    Useful for tracking ingestion progress on large files.
    """
    document_id: str
    filename: str
    file_type: str
    institution_id: str
    status: DocumentStatus
    chunk_count: int
    char_count: int
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
    indexed_at: Optional[datetime]

class DocumentListResponse(BaseModel):
    """
    Returned when listing all documents for an institution.
    """
    documents: list
    total: int
    institution_id: str
