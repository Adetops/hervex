# ingested_document.py defines the MongoDB document shape
# for a file that has been uploaded and ingested into Pinecone.
#
# This is separate from the goal document because it tracks
# a different lifecycle — not an agent run, but a document
# that becomes part of the institution's knowledge base.
#
# Fields:
# document_id: unique ID used as Pinecone namespace prefix
# filename: original uploaded filename
# file_type: pdf or docx
# status: tracks ingestion progress
# chunk_count: how many chunks were stored in Pinecone
# institution_id: which institution this document belongs to
#                 (used for isolation in multi-tenant setup)

from datetime import datetime, timezone
from app.enums.status import DocumentStatus

class IngestedDocument:
    """
    Represents an uploaded document in the MongoDB
    'ingested_documents' collection.
    """

    @staticmethod
    def create(
        document_id: str,
        filename: str,
        file_type: str,
        institution_id: str = "default"
    ) -> dict:
        """
        Builds a new ingested document record for MongoDB.

        Args:
            document_id: Unique ID — also used as Pinecone vector prefix
            filename: Original name of the uploaded file
            file_type: 'pdf' or 'docx'
            institution_id: Institution this document belongs to
                           Defaults to 'default' for single-tenant pilot

        Returns:
            A dictionary representing the MongoDB document
        """
        return {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "institution_id": institution_id,
            "status": DocumentStatus.UPLOADED,
            "chunk_count": 0,        # Updated after Pinecone upsert
            "char_count": 0,         # Updated after text extraction
            "error": None,           # Populated if ingestion fails
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "indexed_at": None,      # Populated when Pinecone upsert completes
        }
