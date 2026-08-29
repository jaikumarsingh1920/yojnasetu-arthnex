from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai import (
    NaturalLanguageExtractRequest,
    NaturalLanguageExtractResponse,
    ClarificationRequest,
    ClarificationResponse,
    AIExplainableRecommendationRequest,
    AIExplainableRecommendationResponse,
    AIChatRequest,
    AIChatResponse,
)
from app.ai.extractor import NaturalLanguageProfileExtractor
from app.ai.clarifier import ConversationalFollowUpService
from app.ai.recommendation_ai import AIExplainableRecommendationService
from app.ai.qa import SchemeQAService
from app.ai.security import AISecurityGuard

router = APIRouter()


@router.post(
    "/profile/extract",
    response_model=NaturalLanguageExtractResponse,
    summary="Extract structured profile from natural language text",
)
def extract_profile_from_text(
    req: NaturalLanguageExtractRequest,
) -> NaturalLanguageExtractResponse:
  """Accepts natural language beneficiary text (e.g.

  'I am a 28 year old SC woman from UP annual income 1.8L...'), extracts
  structured fields, and returns extraction confidence scores while preserving
  UNKNOWN states.
  """
  sanitized_text = AISecurityGuard.sanitize_user_input(req.user_text)
  return NaturalLanguageProfileExtractor.extract_profile(sanitized_text)


@router.post(
    "/profile/clarify",
    response_model=ClarificationResponse,
    summary="Generate targeted follow-up clarification questions",
)
def generate_clarification_questions(
    req: ClarificationRequest,
) -> ClarificationResponse:
  """Evaluates missing high-priority fields in a profile and generates targeted

  clarification questions.
  """
  return ConversationalFollowUpService.generate_clarifications(
      profile=req.extracted_profile, missing_fields_override=req.missing_fields
  )


@router.post(
    "/recommend",
    response_model=AIExplainableRecommendationResponse,
    summary="AI-augmented explainable scheme recommendations",
)
def get_ai_recommendations(
    req: AIExplainableRecommendationRequest, db: Session = Depends(get_db)
) -> AIExplainableRecommendationResponse:
  """Runs natural language profile extraction, deterministic hard eligibility,

  soft-fit scoring, financial calculations, and returns grounded explainable AI
  recommendations with RAG source citations.
  """
  return AIExplainableRecommendationService.get_ai_recommendations(db, req)


from app.ai.agent import GPTCopilotAgent
from app.api.v1.endpoints.ai_stream import router as stream_router

router.include_router(stream_router)


from app.api.deps import get_optional_current_user
from app.models.user import User

@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="YojnaSetu GPT AI Copilot & Scheme Assistant Chat",
)
def chat_with_ai_assistant(
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_current_user)
) -> AIChatResponse:
    """
    GPT-Level YojnaSetu AI Copilot endpoint.
    Multi-turn conversation memory, hybrid RAG reranking, typed tool execution,
    deterministic eligibility/financial engine delegation, source citations & rich response cards.
    """
    user_id = current_user.user_id if current_user else None
    return GPTCopilotAgent.process_query(db, req, current_user_id=user_id)


@router.post(
    "/schemes/{scheme_id}/ask",
    response_model=AIChatResponse,
    summary="Scheme-specific GPT AI Copilot Q&A",
)
def ask_about_specific_scheme(
    scheme_id: str,
    req: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_current_user)
) -> AIChatResponse:
    """
    Scheme-specific GPT AI Copilot endpoint.
    Grounds answers in the specified scheme ID context.
    """
    req.scheme_id = scheme_id
    user_id = current_user.user_id if current_user else None
    return GPTCopilotAgent.process_query(db, req, current_user_id=user_id)
