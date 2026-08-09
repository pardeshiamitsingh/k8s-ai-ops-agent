from langchain_openai import AzureChatOpenAI

from k8s_ai_ops.llm.settings import LLMSettings


def create_azure_model(
    settings: LLMSettings,
) -> AzureChatOpenAI:

    if not settings.azure_endpoint:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT is required"
        )

    if not settings.azure_api_key:
        raise ValueError(
            "AZURE_OPENAI_API_KEY is required"
        )

    if not settings.azure_api_version:
        raise ValueError(
            "AZURE_OPENAI_API_VERSION is required"
        )

    if not settings.azure_deployment:
        raise ValueError(
            "AZURE_OPENAI_DEPLOYMENT is required"
        )

    return AzureChatOpenAI(
        azure_endpoint=settings.azure_endpoint,
        api_key=settings.azure_api_key,
        api_version=settings.azure_api_version,
        azure_deployment=settings.azure_deployment,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )