import json
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_optional_current_user
from app.models.user import User
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.financial_health import (
    FinancialHealthInput,
    FinancialHealthResponse,
)
from app.engine.financial_health import DeterministicFinancialHealthEngine
from app.services.financial_scheme_enrichment_service import FinancialSchemeEnrichmentService

router = APIRouter()


@router.get(
    "/coverage-report",
    status_code=status.HTTP_200_OK,
    summary="Get financial intelligence coverage report across scheme corpus",
    description="Returns audited counts of schemes with financial metadata, loan data, subsidy data, interest data, and calculator readiness."
)
def get_financial_coverage_report(
    db: Session = Depends(get_db)
):
    """
    Returns corpus-wide financial metadata metrics and parameter breakdown.
    """
    return FinancialSchemeEnrichmentService.get_financial_coverage_report(db)



@router.post(
    "/assess",
    response_model=FinancialHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate citizen financial health status deterministically",
    description="Computes transparent debt-service ratio (FOIR), borrowing leverage, financing/margin alignment, and liquidity cushion buffer without black-box AI."
)
def assess_financial_health(
    input_data: FinancialHealthInput,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates financial health suitability based on supplied parameters or citizen profile.
    If no explicit financial values are passed and the request is authenticated,
    automatically falls back to the user's persisted citizen profile.
    """
    # If no values supplied in input_data and authenticated user has saved profile, hydrate from it
    has_explicit_financials = any([
        input_data.annual_income is not None,
        input_data.monthly_income is not None,
        input_data.requested_loan_amount is not None,
        input_data.project_cost is not None,
        input_data.existing_liabilities is not None,
        input_data.monthly_obligations is not None,
        input_data.liquid_savings is not None,
        input_data.profile is not None
    ])

    if not has_explicit_financials and current_user and current_user.profile_data:
        try:
            profile_dict = json.loads(current_user.profile_data)
            input_data.profile = BeneficiaryProfileInput(**profile_dict)
        except Exception:
            pass

    return DeterministicFinancialHealthEngine.evaluate(input_data, db=db)


@router.get(
    "",
    response_model=FinancialHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get financial health status for authenticated user",
    description="Loads authenticated citizen's persisted profile data and calculates deterministic financial suitability indicators and advice."
)
def get_user_financial_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves stored profile for the authenticated user and evaluates their financial health status.
    """
    profile = None
    if current_user.profile_data:
        try:
            profile_dict = json.loads(current_user.profile_data)
            profile = BeneficiaryProfileInput(**profile_dict)
        except Exception:
            profile = None

    input_data = FinancialHealthInput(profile=profile)
    return DeterministicFinancialHealthEngine.evaluate(input_data, db=db)
