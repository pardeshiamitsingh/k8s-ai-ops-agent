from langchain_core.language_models import BaseChatModel

from k8s_ai_ops.llm.factory import LLMFactory
from k8s_ai_ops.llm.settings import LLMSettings


class LLMRuntime:

    def __init__(
        self,
        settings: LLMSettings,
    ):
        self.settings = settings
        self.model: BaseChatModel = (
            LLMFactory.create(settings)
        )

    def get_model(self) -> BaseChatModel:
        return self.model