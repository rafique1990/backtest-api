import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.core.exceptions import PromptParsingError
from app.services.gemini_chat_client import GeminiChatClient
from app.services.openai_chat_client import OpenAIChatClient


class TestOpenAIChatClient:
    @pytest.fixture
    def openai_client(self):
        return OpenAIChatClient(
            api_key="test-key",
            model="gpt-4",
            api_url="https://api.openai.com/v1/chat/completions",
            timeout=30,
        )

    @pytest.mark.asyncio
    async def test_openai_successful_response(self, openai_client):
        """Test successful OpenAI API call."""
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

        # Create a proper async mock response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        # Make json() return the data directly (not a coroutine)
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            openai_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            result = await openai_client.generate_json("test prompt")

            assert result["calendar_rules"]["rule_type"] == "Quarterly"
            assert result["portfolio_creation"]["n"] == 10
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_http_error(self, openai_client):
        """Test OpenAI API HTTP error."""
        # Create a mock that raises HTTP error immediately
        with patch.object(
            openai_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "Error", request=Mock(), response=Mock(status_code=500)
            )

            with pytest.raises(PromptParsingError):
                await openai_client.generate_json("test prompt")

    @pytest.mark.asyncio
    async def test_openai_invalid_json_response(self, openai_client):
        """Test OpenAI API with invalid JSON response."""
        mock_response_data = {"choices": [{"message": {"content": "invalid json {"}}]}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            openai_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(PromptParsingError):
                await openai_client.generate_json("test prompt")

    @pytest.mark.asyncio
    async def test_openai_missing_choices(self, openai_client):
        """Test OpenAI API with missing choices in response."""
        mock_response_data = {"invalid_structure": "no choices field"}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            openai_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(PromptParsingError):
                await openai_client.generate_json("test prompt")


class TestGeminiChatClient:
    @pytest.fixture
    def gemini_client(self):
        return GeminiChatClient(
            api_key="test-key",
            model="gemini-pro",
            api_url="https://generativelanguage.googleapis.com/v1beta",
            timeout=30,
        )

    @pytest.mark.asyncio
    async def test_gemini_successful_response(self, gemini_client):
        """Test successful Gemini API call."""
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "calendar_rules": {
                                            "rule_type": "Quarterly",
                                            "initial_date": "2023-01-01",
                                        },
                                        "portfolio_creation": {
                                            "filter_type": "TopN",
                                            "n": 5,
                                            "data_field": "volume",
                                        },
                                        "weighting_scheme": {"weighting_type": "Equal"},
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            gemini_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            result = await gemini_client.generate_json("test prompt")

            assert result["portfolio_creation"]["data_field"] == "volume"
            assert result["portfolio_creation"]["n"] == 5
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_gemini_missing_candidates(self, gemini_client):
        """Test Gemini API with missing candidates in response."""
        mock_response_data = {"invalid_structure": "no candidates field"}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            gemini_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(PromptParsingError):
                await gemini_client.generate_json("test prompt")

    @pytest.mark.asyncio
    async def test_gemini_empty_candidates(self, gemini_client):
        """Test Gemini API with empty candidates array."""
        mock_response_data = {"candidates": []}

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            gemini_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(PromptParsingError):
                await gemini_client.generate_json("test prompt")

    @pytest.mark.asyncio
    async def test_gemini_missing_parts(self, gemini_client):
        """Test Gemini API with missing parts in candidate."""
        mock_response_data = {
            "candidates": [{"content": {"missing_parts": "no parts field"}}]
        }

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value=mock_response_data)
        mock_response.raise_for_status = Mock()

        with patch.object(
            gemini_client.client, "post", new_callable=AsyncMock
        ) as mock_post:
            mock_post.return_value = mock_response

            with pytest.raises(PromptParsingError):
                await gemini_client.generate_json("test prompt")
