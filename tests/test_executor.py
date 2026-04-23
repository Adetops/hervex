# test_executor.py tests the executor's task processing logic.
# Mocks MongoDB and Redis so tests run without infrastructure.
# Focuses on the executor's decision logic — tool routing,
# failure handling, and status updates.

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_execute_task_with_web_search():
    """
    Tests that a task with tool='web_search' correctly
    calls the web_search tool and returns its result.
    """
    mock_search_result = "Result 1:\nTitle: FastAPI\nURL: https://fastapi.tiangolo.com\nSummary: Modern web framework."

    with patch(
        "app.tools.registry.get_tool",
        return_value=AsyncMock(return_value=mock_search_result)
    ):
        from app.executor.runner import _execute_task
        result = await _execute_task(
            session_id="test-session",
            description="Search for FastAPI documentation",
            tool="web_search"
        )

    assert "FastAPI" in result or result == mock_search_result

@pytest.mark.asyncio
async def test_execute_task_tool_not_found():
    """
    Tests that requesting a non-existent tool raises ValueError.
    """
    with patch("app.executor.runner.get_tool", return_value=None):
        from app.executor.runner import _execute_task

        with pytest.raises(ValueError, match="not found in registry"):
            await _execute_task(
                session_id="test-session",
                description="Do something with a fake tool",
                tool="fake_tool"
            )

@pytest.mark.asyncio
async def test_execute_reasoning_task():
    """
    Tests that a reasoning task (tool=None) calls the LLM
    with memory context and returns a string result.
    Mocks both Redis memory and Groq LLM to run without infrastructure.
    """
    mock_context = "Previous results: Step 1: found FastAPI"
    mock_llm_response = "Based on previous results, FastAPI is the best choice."

    with patch(
        # Patch where runner.py actually calls get_session_context
        "app.executor.runner.get_session_context",
        new_callable=AsyncMock,
        return_value=mock_context
    ), patch(
        "app.executor.runner._llm_client"
    ) as mock_client:
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=mock_llm_response))]
        )

        from app.executor.runner import _execute_task
        result = await _execute_task(
            session_id="test-session",
            description="Summarize what was found",
            tool=None
        )

    assert isinstance(result, str)
    assert result == mock_llm_response
