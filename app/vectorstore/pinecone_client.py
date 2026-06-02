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
# Added institution_id namespace support.
# Each institution's vectors are stored in their own Pinecone namespace.

from pinecone import Pinecone
from typing import List, Dict, Optional
from loguru import logger
from app.core.config import settings
from app.core.settings import RAG_TOP_K, APP_NAME

_pc = Pinecone(api_key=settings.PINECONE_API_KEY)
_index = _pc.Index(settings.PINECONE_INDEX_NAME)


async def upsert_chunks(
    embedded_chunks: List[Dict],
    institution_id: str = "default"
) -> int:
    """
    Uploads embedded chunks to Pinecone under the institution's namespace.
    Each institution's vectors are physically isolated in their own namespace.

    Args:
        embedded_chunks: List of chunk dicts with 'embedding' field
        institution_id: Institution namespace — isolates data per school

    Returns:
        Number of vectors successfully upserted
    """
    if not embedded_chunks:
        raise ValueError("No chunks to upsert")

    vectors = []
    for chunk in embedded_chunks:
        vector_id = f"{chunk['document_id']}_chunk_{chunk['chunk_index']}"
        vectors.append({
            "id": vector_id,
            "values": chunk["embedding"],
            "metadata": {
                "document_id": chunk["document_id"],
                "institution_id": institution_id,
                "chunk_index": chunk["chunk_index"],
                "char_start": chunk["char_start"],
                "text": chunk["text"][:1000]
            }
        })

    batch_size = 100
    total_upserted = 0

    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]

        # namespace= isolates this institution's vectors
        # from all other institutions at the Pinecone level
        _index.upsert(vectors=batch, namespace=institution_id)
        total_upserted += len(batch)
        logger.info(
            f"[{APP_NAME}] Pinecone: Upserted {len(batch)} vectors "
            f"to namespace '{institution_id}'. Total: {total_upserted}"
        )

    return total_upserted


async def query_similar_chunks(
    query_embedding: List[float],
    top_k: int = RAG_TOP_K,
    document_id: Optional[str] = None,
    institution_id: str = "default"
) -> List[Dict]:
    """
    Searches for similar chunks within an institution's namespace only.
    Cross-institution data access is impossible — the namespace
    boundary is enforced at the Pinecone level.

    Args:
        query_embedding: 1536-dimensional query vector
        top_k: Number of results to return
        document_id: Optional filter to one specific document
        institution_id: Institution namespace to search within

    Returns:
        List of matching chunk metadata dictionaries
    """
    logger.info(
        f"[{APP_NAME}] Pinecone: Querying namespace '{institution_id}' "
        f"for top {top_k} chunks"
    )

    query_filter = None
    if document_id:
        query_filter = {"document_id": {"$eq": document_id}}

    response = _index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=query_filter,
        namespace=institution_id  # Hard institution boundary
    )

    results = []
    for match in response.matches:
        results.append({
            "text": match.metadata.get("text", ""),
            "document_id": match.metadata.get("document_id", ""),
            "institution_id": match.metadata.get("institution_id", ""),
            "chunk_index": match.metadata.get("chunk_index", 0),
            "score": match.score
        })

    logger.info(
        f"[{APP_NAME}] Pinecone: Retrieved {len(results)} chunks "
        f"from namespace '{institution_id}'"
    )
    return results


async def delete_document_chunks(
    document_id: str,
    institution_id: str = "default"
) -> bool:
    """
    Deletes all vectors for a document within an institution's namespace.

    Args:
        document_id: Document whose vectors to delete
        institution_id: Institution namespace to delete from

    Returns:
        True if successful
    """
    logger.info(
        f"[{APP_NAME}] Pinecone: Deleting chunks for document "
        f"'{document_id}' in namespace '{institution_id}'"
    )

    _index.delete(
        filter={"document_id": {"$eq": document_id}},
        namespace=institution_id
    )

    logger.info(
        f"[{APP_NAME}] Pinecone: Deleted chunks for "
        f"document '{document_id}'"
    )
    return True
