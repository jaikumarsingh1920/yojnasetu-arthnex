import logging
from sqlalchemy.orm import Session
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.ai.agent import GPTCopilotAgent

logger = logging.getLogger("yojnasetu.ai.qa")


class SchemeQAService:
    """
    Legacy Scheme QA Service delegate.
    Passes all queries directly to the canonical GPTCopilotAgent pipeline.
    """

    @classmethod
    def answer_question(
        cls,
        db: Session,
        req: AIChatRequest
    ) -> AIChatResponse:
        return GPTCopilotAgent.process_query(db, req)
