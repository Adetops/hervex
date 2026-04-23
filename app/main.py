# Entry point of HERVEX. It initializes FastAPI app, registers all routers
# and manages MonogoDB connection lifecycle through FastAPI startup and shutdown events.
# Added: logging setup, exception handlers, rate limiter,
# logs directory creation, and version bumped to 1.0.0.
# HERVEX is now production-ready.


import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routers import goals, health, runs
from app.db.connection import close_mongodb_connection, connect_to_mongodb
from app.core.settings import APP_NAME
from app.core.logging import setup_logging
from app.core.rate_limiter import limiter
from app.exceptions.handlers import register_exception_handlers


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
    description=f"Give {APP_NAME} a goal. It plans, executes, and delivers - autonomously.",
    version="1.0.0",
    lifespan=lifespan
)

# Attach rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Register global exception handlers
register_exception_handlers(app)

app.include_router(goals.router)
app.include_router(runs.router)
app.include_router(health.router)

