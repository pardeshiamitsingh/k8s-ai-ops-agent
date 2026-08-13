from typing import Any

from langchain_core.language_models import BaseChatModel
from langgraph.types import Command

from k8s_ai_ops.graph.workflow import build_workflow
from k8s_ai_ops.models.incident import IncidentRequest


class IncidentService:
    """
    Application service for the complete incident lifecycle.

    Responsibilities:

    1. Start an incident workflow.
    2. Persist workflow execution in LangGraph memory.
    3. Pause at human approval.
    4. Resume the same workflow using thread_id.
    """

    def __init__(
        self,
        llm: BaseChatModel,
    ):
        self.llm = llm

        # Build one compiled LangGraph workflow.
        #
        # The workflow contains the InMemorySaver
        # checkpointer, which allows interrupt/resume.
        self.graph = build_workflow(
            llm
        )

    # ==================================================
    # CREATE INCIDENT
    # ==================================================

    def create_incident(
        self,
        incident: IncidentRequest,
        thread_id: str,
    ) -> dict[str, Any]:
        """
        Start a new incident workflow.

        The workflow will pause at the human approval
        interrupt.
        """

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        initial_state = {
            "incident": incident,
        }

        result = self.graph.invoke(
            initial_state,
            config=config,
        )

        return result

    # ==================================================
    # APPROVE / REJECT
    # ==================================================

    def approve_incident(
        self,
        thread_id: str,
        approved: bool,
        approved_by: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Resume a paused LangGraph workflow.

        The thread_id identifies the exact workflow
        execution that was paused at interrupt().
        """

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        decision = {
            "approved": approved,
            "approved_by": approved_by,
            "reason": reason,
        }

        result = self.graph.invoke(
            Command(
                resume=decision,
            ),
            config=config,
        )

        return result
