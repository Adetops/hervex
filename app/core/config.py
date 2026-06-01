# config.py — updated for education branch
# Added Pinecone and OpenAI keys for RAG pipeline


from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    
    # Groq API key for Llama/Gemma models
    SECRET_GROQ_KEY: str
    
    # Tavily API tool for web search tool
    TAVILY_API_KEY: str
    
    # MongoDB uri string and database name
    MONGODB_URI: str
    MONGODB_DB_NAME: str
    
    # Redis URL used as Celery broker and result backend
    # Celery uses this to queue tasks and store results
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # App environment - "dev" or "prod"
    APP_ENV: str = "development"
    
    PORT: int = 8000
    
    # Pinecone — vector database for institution knowledge
    PINECONE_API_KEY: str
    PINECONE_INDEX_NAME: str = "hervex-education"

    # OpenAI — used only for text embeddings, not chat
    # text-embedding-3-small converts text chunks to 1536-dimensional vectors
    OPENAI_API_KEY: str
    
# single shared instance
settings = Settings()
