from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.recommendation import BeneficiaryProfileInput


class ExtractedFieldConfidence(BaseModel):
  """Provenance and extraction confidence score for an extracted profile field."""

  field: str
  value: Any
  confidence: float = Field(
      ..., ge=0.0, le=1.0, description="Extraction confidence score"
  )
  source_snippet: Optional[str] = Field(
      default=None, description="Verbatim user text snippet"
  )


class NaturalLanguageExtractRequest(BaseModel):
  """Input user text for natural language profile extraction."""

  user_text: str = Field(
      ...,
      min_length=3,
      description="Natural language description of beneficiary profile",
  )


class NaturalLanguageExtractResponse(BaseModel):
  """Extracted structured profile with confidence and missing field annotations."""

  user_text: str
  extracted_profile: BeneficiaryProfileInput
  field_confidences: List[ExtractedFieldConfidence]
  missing_high_priority_fields: List[str]
  fields_requiring_clarification: List[str]
  is_fallback: bool
  provider_name: str


class ClarificationQuestion(BaseModel):
  """A targeted follow-up question to clarify a high-impact missing profile attribute."""

  field: str
  question: str
  options: Optional[List[str]] = None
  impact_reason: str


class ClarificationRequest(BaseModel):
  """Request to evaluate missing high-priority fields and generate clarification questions."""

  extracted_profile: BeneficiaryProfileInput
  missing_fields: Optional[List[str]] = None


class ClarificationResponse(BaseModel):
  """Generated clarification questions and profile completion percentage."""

  questions: List[ClarificationQuestion]
  completion_percentage: float


class SourceCitation(BaseModel):
  """Traceable citation metadata grounding AI responses in authoritative database records."""

  scheme_id: str
  scheme_name: Optional[str] = None
  source_type: str = Field(
      ..., description="SCHEME_METADATA, SCHEME_RULE, SCHEME_DOCUMENT"
  )
  source_document: Optional[str] = None
  rule_id: Optional[str] = None
  snippet: str
  relevance_score: float = Field(..., ge=0.0, le=1.0)


class AICopilotAction(BaseModel):
    label: str = Field(..., description="Button label for UI render")
    action_type: str = Field(..., description="VIEW_SCHEME, CALCULATE_EMI, APPLY_NOW, VIEW_APPLICATION, VIEW_DOCUMENTS")
    target_url: str = Field(..., description="Target route or deep link URL")
    payload: Optional[Dict[str, Any]] = None


class AIChatRequest(BaseModel):
    """Input for AI scheme assistant / Q&A chat endpoint."""
    message: str = Field(..., min_length=2, description="Beneficiary query text")
    session_id: Optional[str] = Field(default=None, description="Session conversation ID")
    scheme_id: Optional[str] = Field(default=None, description="Optional target scheme ID for specific Q&A")
    application_id: Optional[str] = Field(default=None, description="Optional application ID for context")
    page_context: Optional[Dict[str, Any]] = Field(default=None, description="Current page route and metadata")
    profile: Optional[BeneficiaryProfileInput] = Field(default=None, description="Optional beneficiary profile for context")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=None, description="Prior conversation context")
    preferred_language: Optional[str] = Field(default=None, description="Preferred UI language code e.g. hi, bn, te, mr, ta, gu, kn, ml, pa, or, as, en")


class RichCard(BaseModel):
    card_type: str = Field(..., description="SCHEME_CARD, ELIGIBILITY_CARD, FINANCIAL_CARD, DOCUMENT_CHECKLIST, COMPARISON_TABLE, APPLICATION_STATUS_CARD")
    title: str
    subtitle: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class AIChatResponse(BaseModel):
    """Grounding AI response backed by deterministic engines and RAG retrieval."""
    answer: str
    intent: Optional[str] = "GENERAL_SCHEME_QUERY"
    response_mode: Optional[str] = "GROUNDED"
    citations: List[SourceCitation]
    actions: List[AICopilotAction] = []
    rich_cards: List[RichCard] = []
    suggested_questions: List[str] = []
    session_id: Optional[str] = None
    deterministic_used: bool
    financial_calculation: Optional[Dict[str, Any]] = None
    is_fallback: bool
    provider_name: str


class AIExplainableRecommendationRequest(BaseModel):
  """Combined AI + Deterministic Recommendation request."""

  user_text: Optional[str] = Field(
      default=None, description="Natural language profile input"
  )
  profile: Optional[BeneficiaryProfileInput] = Field(
      default=None, description="Structured profile overrides"
  )
  top_k: int = Field(default=5, ge=1, le=20)


class AIRecommendationItem(BaseModel):
  """A single recommended scheme with grounded AI explainability."""

  rank: int
  scheme_id: str
  scheme_name: str
  eligibility_status: str
  score: float
  ai_explanation: str
  matched_factors: List[str]
  eligibility_reasons: List[str]
  financial_fit_summary: str
  citations: List[SourceCitation]


class AIExplainableRecommendationResponse(BaseModel):
  """AI-augmented recommendation response grounded in deterministic backend calculations."""

  evaluated_scheme_count: int
  eligible_scheme_count: int
  recommendations: List[AIRecommendationItem]
  missing_profile_fields: List[str]
  clarification_questions: List[ClarificationQuestion]
  is_fallback: bool
  provider_name: str
