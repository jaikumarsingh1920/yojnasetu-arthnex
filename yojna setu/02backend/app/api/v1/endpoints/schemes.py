import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, asc, desc
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db
from app.models.scheme import Scheme
from app.models.verification import SchemeVerification
from app.schemas.scheme import (
    SchemeListItemResponse,
    PaginatedSchemeListResponse,
    SchemeDetailResponse,
)

router = APIRouter()

# Allowed sort fields to prevent SQL injection / invalid column sorting
ALLOWED_SORT_FIELDS = {
    "scheme_id": Scheme.scheme_id,
    "scheme_name": Scheme.scheme_name,
    "created_at": Scheme.created_at,
    "ministry": Scheme.ministry,
}


@router.get(
    "",
    response_model=PaginatedSchemeListResponse,
    summary="List schemes with search, filtering, and pagination",
    description="Public REST endpoint for scheme discovery. Operates on real PostgreSQL/SQLite scheme dataset."
)
def list_schemes(
    search: Optional[str] = Query(default=None, description="Case-insensitive text search across name, description, purpose, ministry, etc."),
    scheme_type: Optional[str] = Query(default=None, description="Filter by scheme type (e.g. LOAN, MICRO_FINANCE, EDUCATION_LOAN)"),
    ministry: Optional[str] = Query(default=None, description="Filter by ministry"),
    implementing_agency: Optional[str] = Query(default=None, description="Filter by implementing agency"),
    sector: Optional[str] = Query(default=None, description="Filter by sector (e.g. EDUCATION, MULTI_SECTOR)"),
    scheme_status: Optional[str] = Query(default=None, description="Filter by scheme status (e.g. ACTIVE)"),
    marginalized_group: Optional[str] = Query(default=None, description="Filter by marginalized group (e.g. SC)"),
    business_stage: Optional[str] = Query(default=None, description="Filter by business stage"),
    state_restriction: Optional[str] = Query(default=None, description="Filter by state restriction (e.g. ALL_INDIA)"),
    verification_status: Optional[str] = Query(default=None, description="Filter by verification status (e.g. VERIFIED)"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    sort_by: str = Query(default="scheme_id", description="Sort field: scheme_id, scheme_name, created_at, ministry"),
    sort_order: str = Query(default="asc", description="Sort direction: asc or desc"),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of schemes with deterministic database-level filtering,
    case-insensitive search, and stable sorting.
    """
    query = db.query(Scheme)

    # 1. Verification status filter (joins scheme_verifications table)
    if verification_status and verification_status.strip():
        clean_ver = verification_status.strip()
        query = query.join(Scheme.verifications).filter(
            SchemeVerification.verification_status.ilike(f"%{clean_ver}%")
        )

    # 2. Case-insensitive text search across multiple text columns
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Scheme.scheme_name.ilike(term),
                Scheme.short_description.ilike(term),
                Scheme.detailed_description.ilike(term),
                Scheme.purpose.ilike(term),
                Scheme.ministry.ilike(term),
                Scheme.implementing_agency.ilike(term),
                Scheme.sector.ilike(term),
                Scheme.target_beneficiary.ilike(term),
                Scheme.searchable_tags.ilike(term),
            )
        )

    # 3. Specific attribute filters
    if scheme_type and scheme_type.strip():
        query = query.filter(Scheme.scheme_type.ilike(f"%{scheme_type.strip()}%"))

    if ministry and ministry.strip():
        query = query.filter(Scheme.ministry.ilike(f"%{ministry.strip()}%"))

    if implementing_agency and implementing_agency.strip():
        query = query.filter(Scheme.implementing_agency.ilike(f"%{implementing_agency.strip()}%"))

    if sector and sector.strip():
        query = query.filter(Scheme.sector.ilike(f"%{sector.strip()}%"))

    if scheme_status and scheme_status.strip():
        query = query.filter(Scheme.scheme_status.ilike(f"%{scheme_status.strip()}%"))

    if marginalized_group and marginalized_group.strip():
        query = query.filter(Scheme.marginalized_group.ilike(f"%{marginalized_group.strip()}%"))

    if business_stage and business_stage.strip():
        query = query.filter(Scheme.business_stage.ilike(f"%{business_stage.strip()}%"))

    if state_restriction and state_restriction.strip():
        query = query.filter(Scheme.state_restriction.ilike(f"%{state_restriction.strip()}%"))

    # 4. Total matching count
    total = query.count()

    # 5. Sorting
    sort_column = ALLOWED_SORT_FIELDS.get(sort_by.lower(), Scheme.scheme_id)
    order_func = desc if sort_order.lower() == "desc" else asc

    # Apply main sort + secondary sort by scheme_id for guaranteed stable ordering
    if sort_by.lower() != "scheme_id":
        query = query.order_by(order_func(sort_column), asc(Scheme.scheme_id))
    else:
        query = query.order_by(order_func(sort_column))

    # 6. Pagination calculation
    pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return PaginatedSchemeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{scheme_id}",
    response_model=SchemeDetailResponse,
    summary="Get complete scheme detail by scheme_id",
    description="Returns full detailed representation of a scheme including applicable rules, documents, and verification metadata."
)
def get_scheme_detail(
    scheme_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns complete scheme details for a valid scheme_id.
    Eagerly loads related rules, documents, and verifications to prevent N+1 queries.
    Raises HTTP 404 if the scheme_id does not exist.
    """
    scheme = db.query(Scheme).options(
        selectinload(Scheme.verifications),
        selectinload(Scheme.rules),
        selectinload(Scheme.documents),
    ).filter(
        Scheme.scheme_id == scheme_id
    ).first()

    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' was not found.",
        )

    return scheme
