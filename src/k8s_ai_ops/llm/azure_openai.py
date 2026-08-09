from langchain_openai import AzureChatOpenAI


def create_llm():
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
        temperature=0,
    )