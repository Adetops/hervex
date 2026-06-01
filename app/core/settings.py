# settings.py — updated for education branch
# Added chunking and embedding configuration constants

from app.core.config import settings


# Model for planning and task reasoning
LLM_PLANNER_MODEL = "llama-3.3-70b-versatile"

# Model for final response aggregation
# Using the same model keeps things consistent
# Swap to llama-3.1-8b-instant if you hit rate limits
LLM_AGGREGATOR_MODEL = "llama-3.3-70b-versatile"

# Maximum tokens claude can return in a single response
LLM_MAX_TOKENS = 8096

# Maximum number of tasks the planner can generate for a goal
MAX_TASKS_PER_GOAL = 6

# App name to be used in logs and API responses
APP_NAME = "HERVEX"

# Embedding model — OpenAI ada-002 produces 1536-dimensional vectors
# Must match the dimensions set in your Pinecone index
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSIONS = 1536

# Chunking configuration
# CHUNK_SIZE: max characters per chunk sent to Pinecone
# Too large = less precise retrieval
# Too small = loses context
# reliable starting point for academic documents
CHUNK_SIZE = 1000

# CHUNK_OVERLAP: characters shared between consecutive chunks
# Prevents important content from being split across chunk boundaries
CHUNK_OVERLAP = 200

# RAG retrieval configuration
# Number of chunks retrieved from Pinecone per query
# 5 gives enough context without overwhelming the LLM
RAG_TOP_K = 5
