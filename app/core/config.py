# config.py loads env variables from .env file
# and makes them available throughout the application
# pydantic settings ensures all variables are type-checked on start-up.


from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()

class Settings(BaseSettings):
    # Anthropic API key to access Claude LLM
    ANTHROPIC_API_KEY: str
    
    # MongoDB uri string and database name
    MONGODB_URI: str
    MONGODB_DB_NAME: str
    
    # App environment - "dev" or "prod"
    APP_ENV: str = "development"
    
    
    class Config:
        ''' Tells pydantic-settings where to locate .env file
        '''
        
        env_file = ".env"
        extra = "ignore"

# single shared instance
settings = Settings()
