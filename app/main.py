from fastapi import FastAPI
from app.routers import goals, health

app = FastAPI(
    title="HERVEX",
    description="Give HERVEX a goal. It plans, executes, and delivers - autonomously.",
    version="0.1.0"
)

app.include_router(goals.router)
app.include_router(health.router)

