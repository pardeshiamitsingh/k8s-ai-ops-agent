from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


LLMProvider = Literal[
    "azure",
    "bedrock",
    "ollama",
    "fake",
]


class LLMSettings(BaseSettings):
    """
    Centralized LLM configuration.

    Values can come from environment variables or .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: LLMProvider = Field(
        default="fake",
        validation_alias="LLM_PROVIDER",
    )

    model: str | None = Field(
        default=None,
        validation_alias="LLM_MODEL",
    )

    temperature: float = Field(
        default=0.0,
        validation_alias="LLM_TEMPERATURE",
    )

    azure_endpoint: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_ENDPOINT",
    )

    azure_api_key: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_API_KEY",
    )

    azure_api_version: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_API_VERSION",
    )

    azure_deployment: str | None = Field(
        default=None,
        validation_alias="AZURE_OPENAI_DEPLOYMENT",
    )

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_BASE_URL",
    )

    ollama_model: str | None = Field(
        default=None,
        validation_alias="OLLAMA_MODEL",
    )