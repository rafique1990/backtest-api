import logging

from app.core.config import settings
from app.services.gemini_chat_client import GeminiChatClient
from app.services.llm_client_base import BaseChatClient
from app.services.openai_chat_client import OpenAIChatClient

logger = logging.getLogger(__name__)

LLM_CONFIG_MAP: dict[str, tuple[type[BaseChatClient], str, int]] = {
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
        logger.warning(
            f"No API key configured for {provider}. LLM calls will fail if attempted."
        )

    return ClientClass(
        api_key=api_key, model=settings.LLM_MODEL, api_url=base_url, timeout=timeout
    )
