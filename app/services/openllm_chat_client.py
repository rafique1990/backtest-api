import logging
from app.services.llm_client_base import BaseChatClient, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OpenLLMChatClient(BaseChatClient):
    """
    Client for OpenLLM or any OpenAI-compatible API endpoints.
    """

    def __init__(self, api_key: str, model: str, api_url: str, timeout: int):
        super().__init__(api_key, model, api_url, timeout)
        logger.info(
            f"OpenLLMChatClient configured for {self.api_url} with model {self.model}"
        )

    async def _perform_api_call(self, user_prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        response = await self.client.post(self.api_url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        # Validate OpenAI-compatible response structure
        if not response_data.get("choices"):
            raise ValueError("No choices in OpenLLM response")

        if not response_data["choices"][0].get("message"):
            raise ValueError("No message in OpenLLM choice")

        content = response_data["choices"][0]["message"].get("content")
        if not content:
            raise ValueError("No content in OpenLLM message")

        return content
