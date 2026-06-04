# health.py — updated for phase 6
# Enhanced health check now actively pings all critical dependencies
# and returns individual status for each.
# Returns HTTP 200 when all dependencies are healthy.
# Returns HTTP 503 when any critical dependency is unreachable.

from fastapi import APIRouter
from loguru import logger
from app.core.settings import APP_NAME

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """
    Check the health of HERVEX and all critical dependencies.

    Returns HTTP 200 with individual dependency status when healthy.
    Returns HTTP 503 when any critical dependency is unreachable.

    Monitored dependencies:
    - MongoDB — persistent storage
    - Redis — task queue and memory
    - Pinecone — vector database
    - Groq — LLM provider
    """
    from fastapi.responses import JSONResponse

    dependency_status = {
        "mongodb": "unknown",
        "redis": "unknown",
        "pinecone": "unknown",
        "groq": "unknown"
    }

    all_healthy = True

    # Check MongoDB
    try:
        from app.db.connection import get_database
        db = get_database()
        await db.command("ping")
        dependency_status["mongodb"] = "healthy"
    except Exception as e:
        dependency_status["mongodb"] = f"unhealthy: {str(e)[:50]}"
        all_healthy = False
        logger.error(f"[{APP_NAME}] Health: MongoDB unhealthy — {str(e)}")

    # Check Redis
    try:
        import redis.asyncio as aioredis
        from app.core.config import settings
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        dependency_status["redis"] = "healthy"
    except Exception as e:
        dependency_status["redis"] = f"unhealthy: {str(e)[:50]}"
        all_healthy = False
        logger.error(f"[{APP_NAME}] Health: Redis unhealthy — {str(e)}")

    # Check Pinecone
    try:
        from pinecone import Pinecone
        from app.core.config import settings
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        pc.list_indexes()
        dependency_status["pinecone"] = "healthy"
    except Exception as e:
        dependency_status["pinecone"] = f"unhealthy: {str(e)[:50]}"
        all_healthy = False
        logger.error(f"[{APP_NAME}] Health: Pinecone unhealthy — {str(e)}")

    # Check Groq — lightweight check using list models
    try:
        from groq import Groq
        from app.core.config import settings
        client = Groq(api_key=settings.SECRET_GROQ_KEY)
        client.models.list()
        dependency_status["groq"] = "healthy"
    except Exception as e:
        dependency_status["groq"] = f"unhealthy: {str(e)[:50]}"
        # Groq failure is critical — cannot plan or aggregate
        all_healthy = False
        logger.error(f"[{APP_NAME}] Health: Groq unhealthy — {str(e)}")

    response_body = {
        "status": "healthy" if all_healthy else "degraded",
        "service": APP_NAME,
        "version": "1.1.0",
        "dependencies": dependency_status
    }

    status_code = 200 if all_healthy else 503
    return JSONResponse(content=response_body, status_code=status_code)
