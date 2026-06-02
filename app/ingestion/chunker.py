# chunker.py splits extracted document text into overlapping chunks.
# Chunking is critical for RAG quality — chunks that are too large
# retrieve too much irrelevant content, chunks too small lose context.
#
# Why overlapping chunks?
# If an important sentence sits at the boundary between two chunks,
# overlap ensures it appears fully in at least one chunk.
# CHUNK_SIZE=1000 and CHUNK_OVERLAP=200 is a reliable starting point
# for academic documents like schemes of work and lecture notes.
#
# Each chunk is returned as a dictionary with:
# - text: the chunk content
# - chunk_index: position in the document (for ordering)
# - char_start: character offset where this chunk begins

from typing import List, Dict
from loguru import logger
from app.core.settings import CHUNK_SIZE, CHUNK_OVERLAP, APP_NAME


def chunk_text(text: str, document_id: str) -> List[Dict]:
    """
    Splits a full document text into overlapping chunks
    ready for embedding and storage in Pinecone.

    The chunking strategy is character-based with overlap:
    1. Start at position 0
    2. Take CHUNK_SIZE characters
    3. Move forward by (CHUNK_SIZE - CHUNK_OVERLAP) characters
    4. Repeat until end of document

    Args:
        text: Full extracted document text
        document_id: The document's unique ID — embedded in each
                     chunk's metadata for retrieval filtering

    Returns:
        A list of chunk dictionaries, each containing:
        - document_id: links chunk back to its source document
        - chunk_index: position of this chunk in the document
        - char_start: character offset of chunk start
        - text: the actual chunk content

    Raises:
        ValueError: If the text is empty
    """
    if not text or not text.strip():
        raise ValueError("Cannot chunk empty text")

    text = text.strip()
    chunks = []
    start = 0
    chunk_index = 0
    step = CHUNK_SIZE - CHUNK_OVERLAP

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk_text_content = text[start:end]

        # Skip chunks that are just whitespace
        if chunk_text_content.strip():
            chunks.append({
                "document_id": document_id,
                "chunk_index": chunk_index,
                "char_start": start,
                "text": chunk_text_content.strip()
            })
            chunk_index += 1

        # Move forward by step size
        # If we've reached the end, break to avoid infinite loop
        if end >= len(text):
            break

        start += step

    logger.info(
        f"[{APP_NAME}] Chunker: Split document {document_id} "
        f"into {len(chunks)} chunks "
        f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )

    return chunks
