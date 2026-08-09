from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


LLMProvider = Literal[
    "azure",
    "bedrock",
    "ollama",
    "fake",
]


class LLMSettings(BaseModel):
    provider: LLMProvider = "fake"

    model: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None

    # Azure OpenAI
    azure_endpoint: str | None = None
    azure_api_key: str | None = None
    azure_api_version: str | None = None
    azure_deployment: str | None = None

    # AWS Bedrock
    aws_region: str | None = None
    bedrock_model_id: str | None = None

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str | None = None


class AppSettings(BaseSettings):
    """
    Loads application configuration from environment variables
    and .env.
    """

    llm_provider: LLMProvider = "fake"

    llm_model: str | None = None
    llm_temperature: float = 0.0
    llm_max_tokens: int | None = None

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_deployment: str | None = None

    aws_region: str | None = None
    aws_bedrock_model_id: str | None = None

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    def llm_settings(self) -> LLMSettings:
        return LLMSettings(
            provider=self.llm_provider,
            model=self.llm_model,
            temperature=self.llm_temperature,
            max_tokens=self.llm_max_tokens,
            azure_endpoint=self.azure_openai_endpoint,
            azure_api_key=self.azure_openai_api_key,
            azure_api_version=self.azure_openai_api_version,
            azure_deployment=self.azure_openai_deployment,
            aws_region=self.aws_region,
            bedrock_model_id=self.aws_bedrock_model_id,
            ollama_base_url=self.ollama_base_url,
            ollama_model=self.ollama_model,
        )