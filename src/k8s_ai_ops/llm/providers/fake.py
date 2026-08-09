from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class FakeChatModel(BaseChatModel):
    """
    Deterministic model used for unit tests.

    It avoids external LLM calls.
    """

    response: str = "Test response"

    @property
    def _llm_type(self) -> str:
        return "fake"

    def _generate(
        self,
        messages,
        stop=None,
        run_manager=None,
        **kwargs: Any,
    ) -> ChatResult:

        message = AIMessage(
            content=self.response
        )

        generation = ChatGeneration(
            message=message
        )

        return ChatResult(
            generations=[generation]
        )