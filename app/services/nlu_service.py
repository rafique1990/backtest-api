import logging
from typing import Dict, Any

from app.schemas import BacktestRequest
from app.core.exceptions import PromptParsingError
from app.services.llm_factory import get_llm_client

logger = logging.getLogger(__name__)


class NluService:
    def __init__(self):
        self.client = get_llm_client()
        logger.info("NluService initialized with LLM client")

    async def parse_prompt(self, prompt: str) -> BacktestRequest:
        if not prompt or not isinstance(prompt, str):
            raise PromptParsingError("Prompt must be a non-empty string")

        try:
            parsed_data: Dict[str, Any] = await self.client.generate_json(prompt)
            request = BacktestRequest(**parsed_data)

            logger.info(f"Successfully parsed prompt into BacktestRequest")
            return request

        except PromptParsingError:
            raise
        except Exception as e:
            logger.error(f"NLU service error: {e}")
            raise PromptParsingError(f"Failed to process prompt: {e}")
