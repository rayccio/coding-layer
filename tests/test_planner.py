import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock the app modules
mock_app = MagicMock()
mock_app.models.types = MagicMock()
mock_app.services.litellm_service = MagicMock()
mock_app.core.config = MagicMock()
sys.modules['app'] = mock_app
sys.modules['app.models'] = mock_app.models
sys.modules['app.models.types'] = mock_app.models.types
sys.modules['app.services'] = mock_app.services
sys.modules['app.services.litellm_service'] = mock_app.services.litellm_service
sys.modules['app.core'] = mock_app.core
sys.modules['app.core.config'] = mock_app.core.config

# Define dummy HiveTask and HiveTaskStatus
class HiveTaskStatus:
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class DummyHiveTask:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

mock_app.models.types.HiveTask = DummyHiveTask
mock_app.models.types.HiveTaskStatus = HiveTaskStatus

# Mock generate_with_messages to return a valid response for success test
async def mock_generate_success(messages, config):
    return '{"tasks": [{"id": "task_1", "description": "Write code", "agent_type": "backend-developer", "depends_on": [], "required_skills": ["rest_api"]}], "reasoning": "test"}'

mock_app.services.litellm_service.generate_with_messages = mock_generate_success

# Mock settings.secrets.get
mock_app.core.config.settings = MagicMock()
mock_app.core.config.settings.secrets = MagicMock()
mock_app.core.config.settings.secrets.get.return_value = {
    "providers": {
        "openai": {
            "models": {
                "gpt-4o": {"is_primary": True, "enabled": True}
            }
        }
    }
}

from planner.planner import CodingPlanner


@pytest.mark.asyncio
async def test_planner_plan_success():
    planner = CodingPlanner()
    tasks = await planner.plan(
        goal_text="Build a REST API",
        hive_context="",
        skills=[{"id": "sk-1", "name": "rest_api", "description": "Generate REST API code"}],
        roles=["backend-developer"]
    )
    assert len(tasks) == 1
    assert tasks[0].description == "Write code"
    assert tasks[0].agent_type == "backend-developer"
    assert tasks[0].required_skills == ["sk-1"]
    assert tasks[0].loop_handler == "coding_loop"


@pytest.mark.asyncio
async def test_planner_plan_fallback():
    # Simulate API error
    async def mock_generate_fail(*args, **kwargs):
        raise Exception("API error")
    mock_app.services.litellm_service.generate_with_messages = mock_generate_fail

    planner = CodingPlanner()
    tasks = await planner.plan(
        goal_text="Something",
        hive_context="",
        skills=[],
        roles=[]
    )
    assert len(tasks) == 1
    assert tasks[0].description == "Something"
    assert tasks[0].agent_type == "builder"
