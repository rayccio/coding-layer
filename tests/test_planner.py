import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from planner.planner import CodingPlanner

# Define a dummy HiveTask class for the mock
class DummyHiveTask:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.mark.asyncio
async def test_planner_plan_success():
    # Mock the app modules
    with patch.dict('sys.modules', {
        'app': MagicMock(),
        'app.models': MagicMock(),
        'app.models.types': MagicMock(),
        'app.services': MagicMock(),
        'app.services.litellm_service': MagicMock(),
        'app.core': MagicMock(),
        'app.core.config': MagicMock(),
    }):
        # Import inside the patch context
        import sys
        mock_app = sys.modules['app']
        mock_models = mock_app.models
        mock_types = mock_models.types
        mock_litellm = mock_app.services.litellm_service
        mock_core = sys.modules['app.core']
        mock_config = mock_core.config

        # Define HiveTaskStatus class
        class HiveTaskStatus:
            PENDING = "pending"
            ASSIGNED = "assigned"
            RUNNING = "running"
            COMPLETED = "completed"
            FAILED = "failed"
            BLOCKED = "blocked"
            CANCELLED = "cancelled"

        mock_types.HiveTask = DummyHiveTask
        mock_types.HiveTaskStatus = HiveTaskStatus

        # Mock generate_with_messages
        async def mock_generate(messages, config):
            return '{"tasks": [{"id": "task_1", "description": "Write code", "agent_type": "backend-developer", "depends_on": [], "required_skills": ["rest_api"]}], "reasoning": "test"}'
        mock_litellm.generate_with_messages = AsyncMock(side_effect=mock_generate)

        # Mock settings.secrets.get
        mock_settings = MagicMock()
        mock_config.settings = mock_settings
        mock_settings.secrets = MagicMock()
        mock_settings.secrets.get.return_value = {
            "providers": {
                "openai": {
                    "models": {
                        "gpt-4o": {"is_primary": True, "enabled": True}
                    }
                }
            }
        }

        # Create planner and test
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
    with patch.dict('sys.modules', {
        'app': MagicMock(),
        'app.models': MagicMock(),
        'app.models.types': MagicMock(),
        'app.services': MagicMock(),
        'app.services.litellm_service': MagicMock(),
        'app.core': MagicMock(),
        'app.core.config': MagicMock(),
    }):
        import sys
        mock_app = sys.modules['app']
        mock_models = mock_app.models
        mock_types = mock_models.types
        mock_litellm = mock_app.services.litellm_service
        mock_core = sys.modules['app.core']
        mock_config = mock_core.config

        class HiveTaskStatus:
            PENDING = "pending"
            ASSIGNED = "assigned"
            RUNNING = "running"
            COMPLETED = "completed"
            FAILED = "failed"
            BLOCKED = "blocked"
            CANCELLED = "cancelled"

        mock_types.HiveTask = DummyHiveTask
        mock_types.HiveTaskStatus = HiveTaskStatus

        # Simulate an API error
        async def mock_generate_fail(*args, **kwargs):
            raise Exception("API error")
        mock_litellm.generate_with_messages = AsyncMock(side_effect=mock_generate_fail)

        mock_settings = MagicMock()
        mock_config.settings = mock_settings
        mock_settings.secrets = MagicMock()
        mock_settings.secrets.get.return_value = {
            "providers": {
                "openai": {
                    "models": {
                        "gpt-4o": {"is_primary": True, "enabled": True}
                    }
                }
            }
        }

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
