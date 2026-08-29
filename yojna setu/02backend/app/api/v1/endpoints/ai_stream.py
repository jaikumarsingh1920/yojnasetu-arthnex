import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai import AIChatRequest
from app.ai.agent import GPTCopilotAgent

logger = logging.getLogger("yojnasetu.ai.stream")

router = APIRouter()


@router.post(
    "/chat/stream",
    summary="Real-Time Server-Sent Events (SSE) AI Copilot Stream",
)
def stream_chat_with_ai_assistant(
    req: AIChatRequest,
    db: Session = Depends(get_db)
):
    """
    Delivers incremental real-time token chunks via Server-Sent Events (SSE).
    """
    def event_generator():
        try:
            for chunk in GPTCopilotAgent.generate_stream_chunks(db, req):
                data_payload = json.dumps({"chunk": chunk})
                yield f"data: {data_payload}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error("SSE stream error: %s", e, exc_info=True)
            err_payload = json.dumps({"error": "Streaming interrupted. Please try non-streaming fallback."})
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
