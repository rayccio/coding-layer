import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_html_builder():
    from skills.html_builder.version_1.code import run

    with patch.dict(os.environ, {"INTERNAL_API_KEY": "test", "ORCHESTRATOR_URL": "http://test"}):
        # Create an async mock for the response
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"response": "<html>test</html>"})
        mock_response.raise_for_status = MagicMock()

        # Create an async mock for the client
        mock_client = AsyncMock()
        # The post method should return the mock_response
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await run({"description": "a simple page"}, {})
            assert "html" in result
            assert result["html"] == "<html>test</html>"


@pytest.mark.asyncio
async def test_css_styling():
    from skills.css_styling.version_1.code import run

    with patch.dict(os.environ, {"INTERNAL_API_KEY": "test", "ORCHESTRATOR_URL": "http://test"}):
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={"response": "body { color: red; }"})
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await run({"description": "make text red"}, {})
            assert "css" in result
            assert result["css"] == "body { color: red; }"
