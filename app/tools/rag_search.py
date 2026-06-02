# rag_search.py is HERVEX's curriculum intelligence tool.
# It converts a query into a vector embedding, searches Pinecone
# for the most semantically similar document chunks, and returns
# formatted context the LLM can use to answer from school materials.
#
# This is the tool that makes HERVEX different from ChatGPT.
# Instead of answering from generic internet knowledge,
# HERVEX searches the institution's own uploaded documents first.
#
# The tool is registered in the Tool Registry under 'rag_search'
# and is called by the executor when the planner assigns it to a task.
#
# Source labelling:
# All RAG results are clearly marked as "From your school materials"
# so the aggregator can label them correctly in the final response.

from openai import OpenAI
from typing import Optional
from loguru import logger
from app.core.config import settings
from app.core.settings import EMBEDDING_MODEL, RAG_TOP_K, APP_NAME
from app.vectorstore.pinecone_client import query_similar_chunks

# Initialize OpenAI client for embedding generation
# Used only for embeddings — not for chat completions
_openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Minimum similarity score to include a chunk in results
# Scores below this threshold are too loosely related to be useful
# Pinecone cosine similarity scores range from 0 (no match) to 1 (identical)
SIMILARITY_THRESHOLD = 0.75


def _generate_query_embedding(query: str) -> list:
    """
    Converts a text query into a 1536-dimensional vector embedding.
    The same embedding model used during ingestion must be used
    here — mismatched models produce meaningless similarity scores.

    Args:
        query: The student's question or task description

    Returns:
        A list of 1536 floats representing the query's meaning
    """
    response = _openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    return response.data[0].embedding


async def rag_search(
    query: str,
    institution_id: str = "default",
    document_id: Optional[str] = None,
    top_k: int = RAG_TOP_K
) -> str:
    """
    Searches the institution's knowledge base for content
    relevant to the query and returns formatted context.

    This tool is called by the executor when a task requires
    curriculum-grounded information rather than web search.

    Flow:
    1. Convert query to embedding vector
    2. Search Pinecone for similar chunks
    3. Filter by similarity threshold
    4. Format results with source labels
    5. Return context string for LLM consumption

    Args:
        query: The student's question or task description
               (used as the semantic search query)
        institution_id: Which institution's knowledge base to search
                       Ensures cross-institution isolation
        document_id: Optional — restrict search to one specific document
        top_k: Maximum number of chunks to retrieve

    Returns:
        Formatted string of relevant document chunks with source labels.
        Returns a clear "not found" message if nothing relevant exists —
        this prevents HERVEX from hallucinating curriculum content.
    """
    logger.info(
        f"[{APP_NAME}] RAG Search: Searching knowledge base "
        f"for institution '{institution_id}' — query: {query[:80]}..."
    )

    try:
        # Step 1 — Generate query embedding
        query_embedding = _generate_query_embedding(query)

        # Step 2 — Search Pinecone for similar chunks
        results = await query_similar_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=document_id,
            institution_id=institution_id
        )

        # Step 3 — Filter by similarity threshold
        # Chunks below the threshold are too loosely related
        # to be reliable sources for curriculum answers
        relevant_results = [
            r for r in results
            if r.get("score", 0) >= SIMILARITY_THRESHOLD
        ]

        if not relevant_results:
            logger.warning(
                f"[{APP_NAME}] RAG Search: No relevant chunks found "
                f"above threshold {SIMILARITY_THRESHOLD} for query: {query[:80]}"
            )
            # Return a structured "not found" response
            # This is critical — the aggregator uses this to tell
            # the student honestly that the topic isn't in their materials
            return (
                "[FROM SCHOOL MATERIALS — NOT FOUND]\n"
                "I could not find this topic in your school's uploaded materials. "
                "Your school has not uploaded content covering this specific topic. "
                "Would you like me to search the internet for general information instead?"
            )

        # Step 4 — Format results for LLM consumption
        # Each chunk is clearly labelled as school material
        # so the aggregator can maintain source attribution
        formatted_chunks = []
        for i, result in enumerate(relevant_results, 1):
            formatted_chunks.append(
                f"[FROM SCHOOL MATERIALS — Source {i}]\n"
                f"Document ID: {result['document_id']}\n"
                f"Relevance Score: {result['score']:.2f}\n"
                f"Content:\n{result['text']}\n"
            )

        context = "\n---\n".join(formatted_chunks)

        logger.info(
            f"[{APP_NAME}] RAG Search: Retrieved {len(relevant_results)} "
            f"relevant chunks for query"
        )

        return context

    except Exception as e:
        logger.error(f"[{APP_NAME}] RAG Search: Failed — {str(e)}")
        raise
