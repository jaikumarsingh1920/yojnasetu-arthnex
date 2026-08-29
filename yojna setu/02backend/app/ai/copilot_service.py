import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.ai.agent import GPTCopilotAgent

logger = logging.getLogger("yojnasetu.ai.copilot")


class AICopilotService:
    """
    Legacy AICopilotService delegate.
    Passes all queries directly to the canonical GPTCopilotAgent pipeline.
    """

    @classmethod
    def process_chat(
        cls,
        db: Session,
        req: AIChatRequest,
        current_user_id: Optional[str] = None
    ) -> AIChatResponse:
        return GPTCopilotAgent.process_query(db, req, current_user_id)
