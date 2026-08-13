from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from k8s_ai_ops.llm.factory import LLMFactory
from k8s_ai_ops.llm.settings import LLMSettings
from k8s_ai_ops.services.incident_service import IncidentService


@lru_cache
def get_llm() -> BaseChatModel:
    """
    Create and cache the configured LLM.
    """

    settings = LLMSettings()

    return LLMFactory.create(settings)


@lru_cache
def get_incident_service() -> IncidentService:
    """
    Create and cache the IncidentService.

    IncidentService owns the LangGraph workflow and
    incident lifecycle.
    """

    return IncidentService(
        llm=get_llm(),
    )
