import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.exceptions import PromptParsingError
from app.schemas import (
    BacktestRequest,
    CalendarRules,
    PortfolioCreation,
    WeightingScheme,
)

logger = logging.getLogger(__name__)

LLM_SCHEMA = {
    "type": "object",
    "properties": {
        "calendar_rules": CalendarRules.model_json_schema(),
        "portfolio_creation": PortfolioCreation.model_json_schema(),
        "weighting_scheme": WeightingScheme.model_json_schema(),
    },
    "required": ["calendar_rules", "portfolio_creation", "weighting_scheme"],
}

SYSTEM_PROMPT = """
You are a financial AI agent. Analyze natural language backtesting prompts and translate them into strict JSON.

Your response MUST be a JSON object with the following structure:
{
    "calendar_rules": {
        "rule_type": "Quarterly",
        "initial_date": "YYYY-MM-DD"
    },
    "portfolio_creation": {
        "filter_type": "TopN",
        "n": <integer>,
        "data_field": "<string>"
    },
    "weighting_scheme": {
        "weighting_type": "Equal"
    }
}

Rules:
1. Infer missing parameters using defaults (TopN filter, Equal weighting, market_capitalization field)
2. Initial date should be '2023-01-01' if not specified
3. Rule type must always be 'Quarterly'
4. Map 'ADTV' or 'average daily trading volume' to 'adtv_3_month'
5. Respond with only JSON, no explanatory text
"""


class BaseChatClient(ABC):
    """Base class for LLM chat clients with async HTTP support."""

    def __init__(self, api_key: str, model: str, api_url: str, timeout: int):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)
        self.client_name = self.__class__.__name__

    @abstractmethod
    async def _perform_api_call(self, user_prompt: str) -> str:
        """Make API call to LLM provider. Must be implemented by subclasses."""
        pass

    async def generate_json(self, user_prompt: str) -> dict[str, Any]:
        """
        Generate structured JSON from natural language prompt.

        Args:
            user_prompt: Natural language backtest description

        Returns:
            Parsed and validated JSON dict matching BacktestRequest schema

        Raises:
            PromptParsingError: If LLM response is invalid or unparseable
        """
        raw_json_text = "N/A"
        try:
            start_time = time.time()
            raw_json_text = await self._perform_api_call(user_prompt)

            parsed_data = json.loads(raw_json_text)
            BacktestRequest(**parsed_data)

            end_time = time.time()
            logger.info(
                f"{self.client_name} parsing successful. Time: {end_time - start_time:.4f}s"
            )
            return parsed_data

        except httpx.HTTPStatusError as e:
            logger.error(f"{self.client_name} API HTTP error: {e.response.status_code}")
            raise PromptParsingError(f"API Error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"{self.client_name} API request error: {e}")
            raise PromptParsingError("API request failed") from e
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                f"Failed to parse LLM response as JSON: {e}. Raw: {raw_json_text}"
            )
            details = {"raw_llm_output": raw_json_text}
            raise PromptParsingError(
                "LLM response was not valid JSON", details=details
            ) from e
        except (KeyError, IndexError, ValidationError) as e:
            logger.error(
                f"Failed to validate LLM response structure: {e}. Raw: {raw_json_text}"
            )
            details = {"raw_llm_output": raw_json_text}
            raise PromptParsingError(
                "LLM response structure was invalid", details=details
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error during LLM call for {self.client_name}: {e}"
            )
            raise PromptParsingError("Service error during prompt parsing") from e

    async def close(self):
        """Close the async HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
