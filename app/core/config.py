# config.py loads env variables from .env file
# and makes them available throughout the application
# pydantic settings ensures all variables are type-checked on start-up.


from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Groq API key for Llama/Gemma models
    SECRET_GROQ_KEY: str = Field(..., str_strip_whitespace=True)
    
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
    
    
    class Config:
        ''' Tells pydantic-settings where to locate .env file
        '''
        env_file = ".env"
        extra = "ignore"
        env_file_encoding = 'utf-8'

# single shared instance
settings = Settings()
