from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.financial import (
    FinancialCalculationInput,
    FinancialCalculationResult,
)
from app.engine.calculator import DeterministicFinancialEngine

router = APIRouter()


@router.post(
    "/calculate",
    response_model=FinancialCalculationResult,
    status_code=status.HTTP_200_OK,
    summary="Calculate financial terms & amortization schedule",
    description="Calculates financing scenario, EMI, moratorium, beneficiary contribution, and amortization using authoritative scheme rules from database."
)
def calculate_financial_terms(
    calc_input: FinancialCalculationInput,
    db: Session = Depends(get_db)
):
    """
    Evaluates requested financing scenario against scheme-authoritative rules stored in PostgreSQL database.
    """
    return DeterministicFinancialEngine.calculate(db, calc_input)
