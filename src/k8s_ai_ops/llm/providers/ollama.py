from langchain_ollama import ChatOllama

from k8s_ai_ops.llm.settings import LLMSettings


def create_ollama_model(
    settings: LLMSettings,
) -> ChatOllama:
    """
    Create a LangChain Ollama chat model.
    """

    model = (
        settings.ollama_model
        or settings.model
    )

    if not model:
        raise ValueError(
            "OLLAMA_MODEL or LLM_MODEL is required"
        )

    return ChatOllama(
        model=model,
        base_url=settings.ollama_base_url,
        temperature=settings.temperature,
    )