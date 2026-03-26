import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock the worker module completely before importing loop
mock_worker = MagicMock()
mock_worker.loop_handler = MagicMock()
# Provide a dummy BaseLoopHandler
class DummyBaseLoopHandler:
    async def run(self, *args, **kwargs):
        raise NotImplementedError
mock_worker.loop_handler.BaseLoopHandler = DummyBaseLoopHandler

# Provide the required constants
mock_constants = MagicMock()
mock_constants.BUILDER_SOUL = "builder soul"
mock_constants.BUILDER_IDENTITY = "builder identity"
mock_constants.BUILDER_TOOLS = "builder tools"
mock_constants.TESTER_SOUL = "tester soul"
mock_constants.TESTER_IDENTITY = "tester identity"
mock_constants.TESTER_TOOLS = "tester tools"
mock_constants.REVIEWER_SOUL = "reviewer soul"
mock_constants.REVIEWER_IDENTITY = "reviewer identity"
mock_constants.REVIEWER_TOOLS = "reviewer tools"
mock_constants.FIXER_SOUL = "fixer soul"
mock_constants.FIXER_IDENTITY = "fixer identity"
mock_constants.FIXER_TOOLS = "fixer tools"

sys.modules['worker'] = mock_worker
sys.modules['worker.loop_handler'] = mock_worker.loop_handler
sys.modules['worker.constants'] = mock_constants

# Now import the loop module
from loop import CodingLoopHandler


@pytest.mark.asyncio
async def test_coding_loop_handler_structure():
    """Test that the loop handler has the expected method signature."""
    handler = CodingLoopHandler()
    assert hasattr(handler, 'run')
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
    assert mock_save_artifact.call_count >= 3  # code, test result, final


@pytest.mark.asyncio
async def test_coding_loop_handler_failure_after_max_iterations():
    """Simulate repeated failures until max iterations."""
    handler = CodingLoopHandler()
    # Simulate that tests always fail, and fixer never fixes
    call_count = 0
    async def mock_call_ai_delta(agent_id, user_input, model_config, system_prompt_override=None, retries=1):
        nonlocal call_count
        call_count += 1
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

    # Temporarily lower MAX_ITERATIONS for faster test
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
