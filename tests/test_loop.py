import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock the worker module before importing loop
mock_worker = MagicMock()
mock_worker.loop_handler.BaseLoopHandler = object  # dummy base class
sys.modules['worker'] = mock_worker
sys.modules['worker.loop_handler'] = MagicMock()
sys.modules['worker.constants'] = MagicMock()

# Now import the loop module
from loop import CodingLoopHandler


@pytest.mark.asyncio
async def test_coding_loop_handler_structure():
    """Test that the loop handler has the expected method signature."""
    handler = CodingLoopHandler()
    assert hasattr(handler, 'run')
    # The run method should be awaitable
    assert callable(handler.run)


@pytest.mark.asyncio
async def test_coding_loop_handler_max_iterations():
    """Test that MAX_ITERATIONS is set."""
    assert CodingLoopHandler.MAX_ITERATIONS == 5


@pytest.mark.asyncio
async def test_coding_loop_handler_run_success_first_try():
    """Simulate a successful run on first iteration."""
    handler = CodingLoopHandler()
    # Mock the call_ai_delta to return success
    async def mock_call_ai_delta(agent_id, user_input, model_config, system_prompt_override=None, retries=1):
        if "Generate the code" in user_input:
            return "def test_func(): return True"
        elif "Write and run tests" in user_input:
            return '{"passed": true, "errors": []}'
        elif "Review the code" in user_input:
            return '{"issues": [], "approved": true}'
        else:
            return ""

    mock_save_artifact = AsyncMock(return_value={"id": "art-123"})
    mock_update_artifact_status = AsyncMock()

    result = await handler.run(
        agent_id="b-test",
        task_id="t-test",
        description="Write a function that returns True",
        input_data={},
        goal_id="g-test",
        hive_id="h-test",
        project_id="p-test",
        skill_executor=None,
        call_ai_delta=mock_call_ai_delta,
        save_artifact=mock_save_artifact,
        update_artifact_status=mock_update_artifact_status
    )

    assert result["success"] is True
    assert result["iterations"] == 1
    # Check that artifacts were saved
    assert mock_save_artifact.call_count >= 3  # code, test result, final


@pytest.mark.asyncio
async def test_coding_loop_handler_failure_after_max_iterations():
    """Simulate repeated failures until max iterations."""
    handler = CodingLoopHandler()
    # Mock the call_ai_delta to always fail
    async def mock_call_ai_delta(agent_id, user_input, model_config, system_prompt_override=None, retries=1):
        if "Generate the code" in user_input:
            return "def test_func(): return False"
        elif "Write and run tests" in user_input:
            return '{"passed": false, "errors": ["Test failed"]}'
        elif "Review the code" in user_input:
            return '{"issues": ["Bad code"], "approved": false}'
        elif "Provide the fixed code" in user_input:
            return "def test_func(): return True"  # fixed code, but tests still fail? We'll just keep failing
        else:
            return ""

    mock_save_artifact = AsyncMock(return_value={"id": "art-123"})
    mock_update_artifact_status = AsyncMock()

    # We need to patch MAX_ITERATIONS to a small number for speed
    original_max = CodingLoopHandler.MAX_ITERATIONS
    CodingLoopHandler.MAX_ITERATIONS = 2

    try:
        result = await handler.run(
            agent_id="b-test",
            task_id="t-test",
            description="Write a function that returns True",
            input_data={},
            goal_id="g-test",
            hive_id="h-test",
            project_id="p-test",
            skill_executor=None,
            call_ai_delta=mock_call_ai_delta,
            save_artifact=mock_save_artifact,
            update_artifact_status=mock_update_artifact_status
        )
        assert result["success"] is False
        assert result["iterations"] == 2
    finally:
        CodingLoopHandler.MAX_ITERATIONS = original_max
