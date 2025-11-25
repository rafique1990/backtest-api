import logging

from app.services.llm_client_base import SYSTEM_PROMPT, BaseChatClient

logger = logging.getLogger(__name__)


class GeminiChatClient(BaseChatClient):
    def __init__(self, api_key: str, model: str, api_url: str, timeout: int):
        super().__init__(api_key, model, api_url, timeout)
        logger.info(
            f"GeminiChatClient configured for {self.api_url} with model {self.model}"
        )

    async def _perform_api_call(self, user_prompt: str) -> str:
        full_api_url = f"{self.api_url}/{self.model}:generateContent"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "systemInstruction": SYSTEM_PROMPT,
            "generationConfig": {
                "temperature": 0.0,
                "responseMimeType": "application/json",
            },
        }

        response = await self.client.post(full_api_url, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()

        # Add proper error handling for response structure
        if not response_data.get("candidates"):
            raise ValueError("No candidates in Gemini response")

        if not response_data["candidates"][0].get("content"):
            raise ValueError("No content in Gemini candidate")

        if not response_data["candidates"][0]["content"].get("parts"):
            raise ValueError("No parts in Gemini content")

        text = response_data["candidates"][0]["content"]["parts"][0].get("text")
        if not text:
            raise ValueError("No text in Gemini parts")

        return text
