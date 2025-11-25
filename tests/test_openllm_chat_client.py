import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.core.exceptions import PromptParsingError
from app.services.openllm_chat_client import OpenLLMChatClient


class TestOpenLLMChatClient:
    @pytest.fixture
    def openllm_client(self):
        return OpenLLMChatClient(
            api_key="test-key",
            model="test-model",
            api_url="http://localhost:1234/v1/chat/completions",
            timeout=30,
        )

    @pytest.mark.asyncio
    async def test_openllm_successful_response(self, openllm_client):
        """Test successful OpenLLM API call."""
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "calendar_rules": {
                                    "rule_type": "Quarterly",
                                    "initial_date": "2023-01-01",
                                },
                                "portfolio_creation": {
                                    "filter_type": "TopN",
                                    "n": 10,
                                    "data_field": "market_capitalization",
                                },
                                "weighting_scheme": {"weighting_type": "Equal"},
                            }
                        )
                    }
                }
            ]
        }

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            openllm_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            result = await openllm_client.generate_json("test prompt")

            assert result["calendar_rules"]["rule_type"] == "Quarterly"
            assert result["portfolio_creation"]["n"] == 10
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_openllm_http_error(self, openllm_client):
        """Test OpenLLM API HTTP error."""
        with patch.object(
            openllm_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Error", request=Mock(), response=Mock(status_code=500)
            )

            with pytest.raises(PromptParsingError):
                await openllm_client.generate_json("test prompt")

    @pytest.mark.asyncio
    async def test_openllm_invalid_json_response(self, openllm_client):
        """Test OpenLLM API with invalid JSON response."""
        mock_response_data = {"choices": [{"message": {"content": "invalid json {"}}]}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            openllm_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(PromptParsingError):
                await openllm_client.generate_json("test prompt")

    @pytest.mark.asyncio
    async def test_openllm_missing_choices(self, openllm_client):
        """Test OpenLLM API with missing choices in response."""
        mock_response_data = {"invalid_structure": "no choices field"}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            openllm_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(PromptParsingError):
                await openllm_client.generate_json("test prompt")
