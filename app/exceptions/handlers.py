# handlers.py defines custom exception classes and global exception
# handlers for HERVEX. Centralizing error handling here means
# no scattered try/except blocks returning inconsistent error shapes.
#
# FastAPI's exception handler system intercepts raised exceptions
# and converts them into clean, consistent JSON responses.

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

class HERVEXException(Exception):
    """
    Base exception class for all HERVEX-specific errors.
    All custom exceptions inherit from this so they can be
    caught at the global handler level with one handler.
    """
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class GoalNotFoundException(HERVEXException):
    """
    Raised when a goal or run cannot be found by session ID.
    Maps to a 404 HTTP response.
    """
    def __init__(self, session_id: str):
        super().__init__(
            message=f"No goal found for session ID: {session_id}",
            status_code=404
        )

class PlannerException(HERVEXException):
    """
    Raised when the LLM planner fails to return a valid task list.
    Maps to a 422 HTTP response — the input was received but
    could not be processed into a valid plan.
    """
    def __init__(self, detail: str):
        super().__init__(
            message=f"Planner failed to generate tasks: {detail}",
            status_code=422
        )

class ToolNotFoundException(HERVEXException):
    """
    Raised when the executor requests a tool that doesn't exist
    in the Tool Registry.
    Maps to a 500 HTTP response — this is a system configuration error.
    """
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"Tool '{tool_name}' not found in registry.",
            status_code=500
        )

class AggregatorException(HERVEXException):
    """
    Raised when the aggregator fails to synthesize task results.
    Maps to a 500 HTTP response.
    """
    def __init__(self, detail: str):
        super().__init__(
            message=f"Aggregator failed to generate final response: {detail}",
            status_code=500
        )

def register_exception_handlers(app: FastAPI):
    """
    Registers all global exception handlers with the FastAPI app.
    Called once in main.py during app initialization.

    Args:
        app: The FastAPI application instance
    """

    @app.exception_handler(HERVEXException)
    async def hervex_exception_handler(request: Request, exc: HERVEXException):
        """
        Catches all HERVEX custom exceptions and returns
        a consistent JSON error response.
        """
        logger.error(f"HERVEX error on {request.url}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "session_id": None,
                "status": "failed"
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Catches all unhandled exceptions and returns a safe
        500 response without leaking internal details.
        """
        logger.error(f"Unhandled error on {request.url}: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "An unexpected error occurred. Please try again.",
                "session_id": None,
                "status": "failed"
            }
        )
