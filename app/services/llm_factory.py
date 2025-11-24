import logging
from typing import Dict, Type, Tuple

from app.core.config import settings
from app.services.llm_client_base import BaseChatClient
from app.services.openai_chat_client import OpenAIChatClient
from app.services.gemini_chat_client import GeminiChatClient

logger = logging.getLogger(__name__)

LLM_CONFIG_MAP: Dict[str, Tuple[Type[BaseChatClient], str, int]] = {
    "openai": (
        OpenAIChatClient,
        "https://api.openai.com/v1/chat/completions",
        30,
    ),
    "gemini": (
        GeminiChatClient,
        "https://generativelanguage.googleapis.com/v1beta",
        30,
    ),
}


def get_llm_client() -> BaseChatClient:
    provider = settings.LLM_PROVIDER.lower()

    if provider not in LLM_CONFIG_MAP:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    ClientClass, base_url, timeout = LLM_CONFIG_MAP[provider]
    api_key = settings.ACTIVE_LLM_API_KEY.get_secret_value()

    if not api_key:
        raise ValueError(f"API key required for {provider}")

    return ClientClass(
        api_key=api_key, model=settings.LLM_MODEL, api_url=base_url, timeout=timeout
    )
