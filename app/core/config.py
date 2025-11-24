from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from typing import Literal, Any
from pydantic.fields import PrivateAttr


class LLMConfigMixin:
    _active_llm_api_key: SecretStr = PrivateAttr(SecretStr(""))

    def model_post_init(self, context: Any) -> None:
        provider_key_map = {
            "openai": self.OPENAI_API_KEY,
            "gemini": self.GEMINI_API_KEY,
        }
        active_key = provider_key_map.get(self.LLM_PROVIDER)
        if active_key and active_key.get_secret_value():
            self._active_llm_api_key = active_key

    @property
    def ACTIVE_LLM_API_KEY(self) -> SecretStr:
        return self._active_llm_api_key


class Settings(LLMConfigMixin, BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "bitacore-backtest"
    ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    LLM_PROVIDER: Literal["openai", "gemini"] = "openai"
    LLM_MODEL: str = "gpt-4-turbo-preview"

    OPENAI_API_KEY: SecretStr = Field(default=SecretStr(""))
    GEMINI_API_KEY: SecretStr = Field(default=SecretStr(""))

    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_DATA_DIR: str = "./data"
    AWS_REGION: str = "us-east-1"
    S3_BUCKET: str = ""


settings = Settings()
