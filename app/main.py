# main.py — updated for education branch
# Added documents router for document ingestion endpoints
# All routers now use /v1/ versioning as per SRS.
# Old unversioned routers removed.
# Feedback router added.
# Health check remains unversioned at /health.


import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.db.connection import close_mongodb_connection, connect_to_mongodb
from app.core.settings import APP_NAME
from app.core.logging import setup_logging
from app.core.rate_limiter import limiter
from app.exceptions.handlers import register_exception_handlers
from app.routers import health
from app.routers.v1 import documents, goals, runs, feedback


# Ensure logs directory exists before logging initializes
os.makedirs("logs", exist_ok=True)

# Initialize structured logging
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from loguru import logger
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()

app = FastAPI(
    title=APP_NAME,
    description=(
        "HERVEX — AI Education Infrastructure. "
        "Give HERVEX a goal. It plans, executes using your school's "
        "own materials, and delivers — autonomously."
    ),
    version="1.0.0",
    lifespan=lifespan
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register global exception handlers
register_exception_handlers(app)

app.include_router(goals.router)
app.include_router(runs.router)
app.include_router(documents.router)
app.include_router(feedback.router)

# Unversioned
app.include_router(health.router)

