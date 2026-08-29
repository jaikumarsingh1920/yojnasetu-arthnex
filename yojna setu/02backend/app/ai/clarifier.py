from typing import List, Optional
from app.schemas.recommendation import BeneficiaryProfileInput
from app.schemas.ai import ClarificationQuestion, ClarificationResponse


class ConversationalFollowUpService:
  """Evaluates missing profile fields and generates target clarification questions."""

  # High impact field questions catalog
  FIELD_CATALOG = {
      "age": {
          "question": "What is your current age?",
          "options": ["18-30 years", "31-45 years", "46-60 years", "Above 60"],
          "impact_reason": (
              "Required for age-restricted subsidy schemes (e.g. NSFDC Youth"
              " Schemes, PMEGP age limits)."
          ),
      },
      "annual_income": {
          "question": "What is your approximate annual household income?",
          "options": [
              "Below ₹1.5 Lakh",
              "₹1.5 Lakh - ₹3 Lakh",
              "₹3 Lakh - ₹6 Lakh",
              "Above ₹6 Lakh",
          ],
          "impact_reason": (
              "Determines micro-finance income eligibility caps (e.g."
              " NBCFDC/NSFDC ceiling ₹3 Lakhs)."
          ),
      },
      "social_category": {
          "question": (
              "Which social category do you belong to (General, SC, ST, OBC)?"
          ),
          "options": ["SC", "ST", "OBC", "GENERAL", "EWS"],
          "impact_reason": (
              "Unlocks dedicated equity, concession, and interest subsidy"
              " schemes (e.g. NSFDC for SC, NBCFDC for OBC)."
          ),
      },
      "state": {
          "question": "Which State or Union Territory do you reside in?",
          "options": [
              "Uttar Pradesh",
              "Maharashtra",
              "Bihar",
              "Madhya Pradesh",
              "Rajasthan",
              "Gujarat",
              "Other State",
          ],
          "impact_reason": (
              "Filters state-specific vs national schemes and regional quota"
              " allocations."
          ),
      },
      "sector": {
          "question": "What business sector or activity are you planning?",
          "options": [
              "Micro Finance / Small Business",
              "Agriculture / Allied",
              "Manufacturing",
              "Services / Trading",
          ],
          "impact_reason": (
              "Determines sectoral subsidy eligibility under PMEGP, Mudra, or"
              " NBCFDC term loans."
          ),
      },
      "project_cost": {
          "question": "What is the total estimated cost of your project?",
          "options": [
              "Under ₹1 Lakh",
              "₹1 Lakh - ₹5 Lakhs",
              "₹5 Lakhs - ₹10 Lakhs",
              "Above ₹10 Lakhs",
          ],
          "impact_reason": (
              "Matches scheme minimum/maximum financial project cost thresholds."
          ),
      },
      "requested_loan_amount": {
          "question": "How much loan financing are you seeking?",
          "options": [
              "Under ₹50,000",
              "₹50,000 - ₹2 Lakhs",
              "₹2 Lakhs - ₹5 Lakhs",
              "Above ₹5 Lakhs",
          ],
          "impact_reason": (
              "Calculates exact loan-to-cost ratio and channelizing agency"
              " sanction limits."
          ),
      },
      "gender": {
          "question": "What is your gender?",
          "options": ["Female", "Male", "Transgender"],
          "impact_reason": (
              "Required for women-focused concession schemes (e.g. Mahila"
              " Samriddhi Yojana, Stand-Up India)."
          ),
      },
  }

  @classmethod
  def generate_clarifications(
      self,
      profile: BeneficiaryProfileInput,
      missing_fields_override: Optional[List[str]] = None,
  ) -> ClarificationResponse:
    all_fields = list(self.FIELD_CATALOG.keys())

    if missing_fields_override is not None:
      missing = missing_fields_override
    else:
      missing = [f for f in all_fields if getattr(profile, f, None) is None]

    present_count = len(all_fields) - len(missing)
    completion_percentage = round((present_count / len(all_fields)) * 100.0, 1)

    questions: List[ClarificationQuestion] = []
    for field_name in missing[:4]:  # Top 4 highest impact missing fields
      if field_name in self.FIELD_CATALOG:
        info = self.FIELD_CATALOG[field_name]
        questions.append(
            ClarificationQuestion(
                field=field_name,
                question=info["question"],
                options=info.get("options"),
                impact_reason=info["impact_reason"],
            )
        )

    return ClarificationResponse(
        questions=questions, completion_percentage=completion_percentage
    )
