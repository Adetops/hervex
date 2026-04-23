# connection.py manages mongodb connection lifecycle for hervex

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.settings import APP_NAME
from loguru import logger


# Global mongoDB client instance
client: AsyncIOMotorClient = None

async def connect_to_mongodb():
    ''' Opens mongodb connection when hervex starts up
    '''
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    logger.info("Connected to MongoDB successfully!")


async def close_mongodb_connection():
    ''' closes mongodb connection when hervex shut down
    '''
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed.")


def get_database():
    """
    Returns the active database instance
    Used as a dependency in service and connection layers
    """
    return client[settings.MONGODB_DB_NAME]
