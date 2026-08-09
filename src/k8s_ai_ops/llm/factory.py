from langchain_core.language_models import BaseChatModel

from k8s_ai_ops.llm.providers.azure import (
    create_azure_model,
)
from k8s_ai_ops.llm.providers.bedrock import (
    create_bedrock_model,
)
from k8s_ai_ops.llm.providers.fake import (
    FakeChatModel,
)
from k8s_ai_ops.llm.providers.ollama import (
    create_ollama_model,
)
from k8s_ai_ops.llm.settings import (
    LLMSettings,
)


class LLMFactory:

    @staticmethod
    def create(
        settings: LLMSettings,
    ) -> BaseChatModel:

        match settings.provider:

            case "azure":
                return create_azure_model(settings)

            case "bedrock":
                return create_bedrock_model(settings)

            case "ollama":
                return create_ollama_model(settings)

            case "fake":
                return FakeChatModel()

            case _:
                raise ValueError(
                    f"Unsupported LLM provider: "
                    f"{settings.provider}"
                )