# pinecone_client.py manages all interactions with Pinecone.
# Pinecone is a cloud vector database — it stores embeddings
# and enables fast semantic similarity search.
#
# How Pinecone works in HERVEX:
# UPSERT: When a document is ingested, its chunk embeddings
#         are uploaded to Pinecone with metadata
# QUERY:  When a student submits a goal, rag_search converts
#         the query to an embedding and finds the most similar
#         chunks in Pinecone — returning relevant document content
#
# Each vector in Pinecone has:
# - id: unique string (document_id + chunk_index)
# - values: the 1536-dimensional embedding vector
# - metadata: document_id, chunk_index, text content


from pinecone import Pinecone
from typing import List, Dict, Optional
from loguru import logger
from app.core.config import settings
from app.core.settings import RAG_TOP_K, APP_NAME

# Initialize Pinecone client
# Pinecone() reads PINECONE_API_KEY from settings
_pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Get the index — must already exist in your Pinecone dashboard
# Index name, dimensions, and metric are set during index creation
_index = _pc.Index(settings.PINECONE_INDEX_NAME)


async def upsert_chunks(embedded_chunks: List[Dict]) -> int:
    """
    Uploads embedded chunks to Pinecone.
    Each chunk becomes one vector in the index.

    Upsert means insert-or-update — if a vector with the
    same ID already exists it is overwritten. This allows
    re-ingesting a document without creating duplicates.

    Args:
        embedded_chunks: List of chunk dicts with 'embedding' field
                         from embedder.py

    Returns:
        Number of vectors successfully upserted

    Raises:
        Exception: If Pinecone upsert fails
    """
    if not embedded_chunks:
        raise ValueError("No chunks to upsert")

    # Build Pinecone vector records
    # Each record: (id, values, metadata)
    vectors = []
    for chunk in embedded_chunks:
        vector_id = f"{chunk['document_id']}_chunk_{chunk['chunk_index']}"

        vectors.append({
            "id": vector_id,
            "values": chunk["embedding"],
            "metadata": {
                # Store text in metadata for retrieval
                # Pinecone returns metadata with search results
                "document_id": chunk["document_id"],
                "chunk_index": chunk["chunk_index"],
                "char_start": chunk["char_start"],
                "text": chunk["text"][:1000]  # Pinecone metadata limit
            }
        })

    # Upsert in batches of 100
    # Pinecone recommends batches for large uploads
    batch_size = 100
    total_upserted = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        _index.upsert(vectors=batch)
        total_upserted += len(batch)
        logger.info(
            f"[{APP_NAME}] Pinecone: Upserted batch of "
            f"{len(batch)} vectors. Total: {total_upserted}"
        )

    logger.info(
        f"[{APP_NAME}] Pinecone: Successfully stored "
        f"{total_upserted} vectors"
    )
    return total_upserted


async def query_similar_chunks(
    query_embedding: List[float],
    top_k: int = RAG_TOP_K,
    document_id: Optional[str] = None
) -> List[Dict]:
    """
    Searches Pinecone for chunks most semantically similar
    to the query embedding.

    Used by rag_search tool during agent task execution.
    The query embedding is generated from the student's
    question or task description.

    Args:
        query_embedding: 1536-dimensional vector from OpenAI
        top_k: Number of most similar chunks to return
        document_id: Optional filter — restrict search to
                     chunks from one specific document

    Returns:
        List of matching chunk metadata dictionaries,
        each containing 'text', 'document_id', 'chunk_index',
        and 'score' (similarity score 0-1)
    """
    logger.info(
        f"[{APP_NAME}] Pinecone: Querying for top {top_k} similar chunks"
    )

    # Build filter if document_id is specified
    # This restricts results to a specific document's chunks
    query_filter = None
    if document_id:
        query_filter = {"document_id": {"$eq": document_id}}

    response = _index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,  # Returns chunk text in results
        filter=query_filter
    )

    results = []
    for match in response.matches:
        results.append({
            "text": match.metadata.get("text", ""),
            "document_id": match.metadata.get("document_id", ""),
            "chunk_index": match.metadata.get("chunk_index", 0),
            "score": match.score
        })

    logger.info(
        f"[{APP_NAME}] Pinecone: Retrieved {len(results)} chunks"
    )
    return results


async def delete_document_chunks(document_id: str) -> bool:
    """
    Deletes all vectors belonging to a specific document.
    Called when a document is removed from the system.
    Uses Pinecone's metadata filter to target only
    vectors from the specified document.

    Args:
        document_id: The document whose vectors to delete

    Returns:
        True if deletion was successful
    """
    logger.info(
        f"[{APP_NAME}] Pinecone: Deleting all chunks "
        f"for document {document_id}"
    )

    _index.delete(filter={"document_id": {"$eq": document_id}})
    logger.info(
        f"[{APP_NAME}] Pinecone: Deleted chunks "
        f"for document {document_id}"
    )
    return True
