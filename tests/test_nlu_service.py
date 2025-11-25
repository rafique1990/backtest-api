import logging
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import PromptParsingError
from app.schemas import BacktestRequest
from app.services.nlu_service import NluService

logger = logging.getLogger(__name__)


class TestNluService:
    @pytest.fixture
    def mock_llm_client(self):
        mock_client = AsyncMock()
        mock_client.generate_json = AsyncMock()
        return mock_client

    @pytest.fixture
    def nlu_service(self, mock_llm_client):
        with patch(
            "app.services.nlu_service.get_llm_client", return_value=mock_llm_client
        ):
            return NluService()

    @pytest.mark.asyncio
    async def test_parse_prompt_success(self, nlu_service, mock_llm_client):
        """Test successful prompt parsing with valid LLM response."""
        # Mock LLM response
        mock_response = {
            "calendar_rules": {"rule_type": "Quarterly", "initial_date": "2023-01-01"},
            "portfolio_creation": {
                "filter_type": "TopN",
                "n": 10,
                "data_field": "market_capitalization",
            },
            "weighting_scheme": {"weighting_type": "Equal"},
        }
        mock_llm_client.generate_json.return_value = mock_response

        # Test prompt
        prompt = "Run a backtest starting from 2023-01-01 with top 10 securities"
        result = await nlu_service.parse_prompt(prompt)

        # Assertions
        assert isinstance(result, BacktestRequest)
        assert result.calendar_rules.rule_type == "Quarterly"
        assert result.calendar_rules.initial_date.isoformat() == "2023-01-01"
        assert result.portfolio_creation.n == 10
        assert result.portfolio_creation.data_field == "market_capitalization"
        mock_llm_client.generate_json.assert_called_once_with(prompt)

    @pytest.mark.asyncio
    async def test_parse_prompt_invalid_response(self, nlu_service, mock_llm_client):
        """Test prompt parsing with invalid LLM response."""
        mock_llm_client.generate_json.return_value = {
            "invalid_field": "invalid_value"  # Missing required fields
        }

        prompt = "Run a backtest"

        with pytest.raises(PromptParsingError):
            await nlu_service.parse_prompt(prompt)

    @pytest.mark.asyncio
    async def test_parse_prompt_llm_error(self, nlu_service, mock_llm_client):
        """Test prompt parsing when LLM service fails."""
        mock_llm_client.generate_json.side_effect = Exception("LLM API error")

        prompt = "Run a backtest"

        with pytest.raises(PromptParsingError):
            await nlu_service.parse_prompt(prompt)

    @pytest.mark.asyncio
    async def test_parse_prompt_empty_string(self, nlu_service):
        """Test prompt parsing with empty string."""
        with pytest.raises(
            PromptParsingError, match="Prompt must be a non-empty string"
        ):
            await nlu_service.parse_prompt("")

    @pytest.mark.asyncio
    async def test_parse_prompt_none(self, nlu_service):
        """Test prompt parsing with None."""
        with pytest.raises(
            PromptParsingError, match="Prompt must be a non-empty string"
        ):
            await nlu_service.parse_prompt(None)

    @pytest.mark.asyncio
    async def test_parse_prompt_different_data_fields(
        self, nlu_service, mock_llm_client
    ):
        """Test prompt parsing with different data field requests."""
        test_cases = [
            {"prompt": "backtest with volume data", "expected_field": "volume"},
            {"prompt": "use ADTV for selection", "expected_field": "adtv_3_month"},
            {"prompt": "backtest with prices", "expected_field": "prices"},
        ]

        for test_case in test_cases:
            mock_llm_client.generate_json.return_value = {
                "calendar_rules": {
                    "rule_type": "Quarterly",
                    "initial_date": "2023-01-01",
                },
                "portfolio_creation": {
                    "filter_type": "TopN",
                    "n": 5,
                    "data_field": test_case["expected_field"],
                },
                "weighting_scheme": {"weighting_type": "Equal"},
            }

            result = await nlu_service.parse_prompt(test_case["prompt"])
            assert result.portfolio_creation.data_field == test_case["expected_field"]
