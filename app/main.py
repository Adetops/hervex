# Entry point of HERVEX. It initializes FastAPI app, registers all routers
# and manages MonogoDB connection lifecycle through FastAPI startup and shutdown events.

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import goals, health, runs
from app.db.connection import close_mongodb_connection, connect_to_mongodb
from app.core.settings import APP_NAME

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongodb()
    yield
    await close_mongodb_connection()

app = FastAPI(
    title=APP_NAME,
    description=f"Give {APP_NAME} a goal. It plans, executes, and delivers - autonomously.",
    version="0.7.0",
    lifespan=lifespan
)

app.include_router(goals.router)
app.include_router(runs.router)
app.include_router(health.router)

