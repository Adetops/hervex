# embedder.py converts text chunks into vector embeddings
# using OpenAI's text-embedding-3-small model.
#
# Why OpenAI embeddings?
# 3-small produces 1536-dimensional vectors that match our
# Pinecone index dimensions. It is reliable, fast, and the
# most widely used embedding model for RAG pipelines.
# We use it only for embeddings — not for chat completions.
#
# Each chunk is embedded individually.
# The resulting vectors are stored in Pinecone alongside
# the chunk metadata for retrieval during RAG queries.

from openai import OpenAI
from typing import List, Dict
from loguru import logger
from app.core.config import settings
from app.core.settings import EMBEDDING_MODEL, APP_NAME

# Initialize OpenAI client
# Used only for the Embeddings API, not chat completions
_openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Converts a list of text chunks into vector embeddings.
    Each chunk dictionary is updated with its embedding vector.

    Processes chunks in batches of 100 to stay within
    OpenAI's API limits while minimising total API calls.

    Args:
        chunks: List of chunk dictionaries from chunker.py
                Each must have a 'text' field

    Returns:
        The same list of chunks, each now containing an
        'embedding' field with a list of 1536 floats

    Raises:
        ValueError: If chunks list is empty
        Exception: If OpenAI API call fails
    """
    if not chunks:
        raise ValueError("Cannot embed empty chunk list")

    logger.info(
        f"[{APP_NAME}] Embedder: Embedding {len(chunks)} chunks "
        f"using {EMBEDDING_MODEL}"
    )

    # Process in batches of 100
    # OpenAI allows up to 2048 inputs per request
    # but smaller batches are safer for error recovery
    batch_size = 100
    embedded_chunks = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [chunk["text"] for chunk in batch]

        logger.info(
            f"[{APP_NAME}] Embedder: Processing batch "
            f"{i // batch_size + 1} — {len(batch)} chunks"
        )

        # Call OpenAI Embeddings API
        # Returns one embedding vector per input text
        response = _openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )

        # Attach each embedding to its corresponding chunk
        for j, embedding_data in enumerate(response.data):
            chunk = batch[j].copy()
            chunk["embedding"] = embedding_data.embedding
            embedded_chunks.append(chunk)

    logger.info(
        f"[{APP_NAME}] Embedder: Successfully embedded "
        f"{len(embedded_chunks)} chunks"
    )

    return embedded_chunks
