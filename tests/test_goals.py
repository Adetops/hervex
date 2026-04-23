# test_goals.py — updated to properly disable rate limiting during tests.
# slowapi requires app.state.limiter to be set before any request.
# We override the limiter with a no-op version for the test client
# so tests run without Redis and without rate limit interference.

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.main import app
from app.enums.status import GoalStatus, Priority
from datetime import datetime, timezone

# Replace the real limiter with a no-op limiter that never hits Redis
# This must happen before the TestClient is created
app.state.limiter = Limiter(
    key_func=get_remote_address,
    # No storage_uri — uses in-memory storage, no Redis needed
)

client = TestClient(app, raise_server_exceptions=False)

def test_submit_goal_success():
    """
    Tests that a valid goal submission returns 201
    with a session ID and correct response shape.
    """
    mock_response = {
        "session_id": "test-session-123",
        "goal": "Find the top 3 Python frameworks and summarize them",
        "status": GoalStatus.PLANNING,
        "priority": Priority.NORMAL,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": "HERVEX has planned 5 tasks. Poll /runs/test-session-123 for progress."
    }

    with patch(
        "app.routers.goals.create_goal",
        new_callable=AsyncMock,
        return_value=mock_response
    ), patch(
        "app.db.connection.connect_to_mongodb",
        new_callable=AsyncMock
    ):
        response = client.post(
            "/goals/",
            json={
                "goal": "Find the top 3 Python frameworks and summarize them",
                "priority": "normal"
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["status"] == GoalStatus.PLANNING

def test_submit_goal_too_short():
    """
    Tests that a goal shorter than 10 characters
    is rejected with a 422 validation error.
    """
    response = client.post(
        "/goals/",
        json={
            "goal": "Too short",
            "priority": "normal"
        }
    )
    assert response.status_code == 422

def test_health_endpoint():
    """
    Tests that the health check endpoint returns 200
    and confirms the API is online.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
