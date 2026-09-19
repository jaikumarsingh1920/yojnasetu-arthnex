from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.partner import (
    PaginatedPartnerApplicationListResponse,
    PartnerApplicationDetailResponse,
    NearestPartnerResponse,
    PartnerRoutingAuditResponse,
    PartnerCoverageReportResponse,
    PartnerFinancialHealthResponse,
    DocumentReviewRequest,
    DocumentReviewResponse,
    ApplicationAssignmentRequest,
    ApplicationReviewNoteCreateRequest,
    ApplicationReviewNoteResponse,
    ApplicationReviewDecisionRequest,
    ApprovalReadinessResponse,
    RequestCorrectionRequest,
    SchemeFinancialSummaryResponse,
    SchemeFinancialDetailResponse,
)
from app.services.partner_service import PartnerService
from app.services.geo_partner_service import GeoPartnerLocatorService
from app.services.channel_partner_enrichment_service import ChannelPartnerEnrichmentService

router = APIRouter()


@router.get(
    "/coverage-report",
    response_model=PartnerCoverageReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get channel partner and scheme coverage statistics",
    description="Returns aggregate metrics on schemes, channel partners, geocoding coverage, partner types, and distribution."
)
def get_channel_partner_coverage_report(
    db: Session = Depends(get_db)
):
    """
    Returns verified channel partner coverage metrics across the scheme corpus.
    """
    return ChannelPartnerEnrichmentService.get_coverage_report(db)


@router.get(
    "/routing-audit",
    response_model=PartnerRoutingAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Get channel partner routing evaluation and structured exclusion audit",
    description="Returns both recommended channel partners and excluded candidates with structured statutory prudential explanations."
)
def get_partner_routing_audit(
    latitude: float = Query(..., description="Citizen's latitude"),
    longitude: float = Query(..., description="Citizen's longitude"),
    radius_km: float = Query(100.0, description="Search radius in km"),
    max_npa: float = Query(10.0, description="Maximum acceptable NPA percentage"),
    partner_type: Optional[str] = Query(None, description="Filter by partner type"),
    partner_category: Optional[str] = Query(None, description="Filter by category"),
    district: Optional[str] = Query(None, description="Filter by district"),
    state: Optional[str] = Query(None, description="Filter by state"),
    pincode: Optional[str] = Query(None, description="Filter by postal PIN code"),
    scheme_id: Optional[str] = Query(None, description="Filter by compatible scheme"),
    loan_category: Optional[str] = Query(None, description="Filter by loan category"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    limit: int = Query(50, ge=1, le=100, description="Max recommended results"),
    db: Session = Depends(get_db)
):
    """
    Executes multi-signal candidate routing with structured exclusion audit.
    """
    return GeoPartnerLocatorService.find_partners_with_routing_audit(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        max_npa=max_npa,
        partner_type=partner_type,
        partner_category=partner_category,
        district=district,
        state=state,
        pincode=pincode,
        scheme_id=scheme_id,
        loan_category=loan_category,
        service_type=service_type,
        limit=limit
    )


@router.get(
    "/nearest",
    response_model=List[NearestPartnerResponse],
    status_code=status.HTTP_200_OK,
    summary="Find nearest channel partners",
    description="Returns a list of active, eligible channel partners sorted by proximity and scheme suitability, filtered by statutory prudential rules."
)
def get_nearest_partners(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius_km: float = Query(100.0, description="Search radius in km"),
    max_npa: float = Query(10.0, description="Maximum acceptable NPA percentage"),
    partner_type: Optional[str] = Query(None, description="Filter by partner type"),
    partner_category: Optional[str] = Query(None, description="Filter by category (AUTHORIZED_SCHEME_PARTNER, IMPLEMENTING_ASSISTANCE_CENTRE, NEARBY_FINANCIAL_SERVICE_POINT)"),
    district: Optional[str] = Query(None, description="Filter by district (e.g. Gorakhpur, Lucknow)"),
    state: Optional[str] = Query(None, description="Filter by state (e.g. Uttar Pradesh)"),
    pincode: Optional[str] = Query(None, description="Filter by postal PIN code (e.g. 273001)"),
    scheme_id: Optional[str] = Query(None, description="Filter by compatible scheme"),
    loan_category: Optional[str] = Query(None, description="Filter by loan category"),
    service_type: Optional[str] = Query(None, description="Filter by service type"),
    include_excluded: bool = Query(False, description="Include excluded partners with structured exclusion reasons"),
    limit: int = Query(100, ge=1, le=100, description="Max results"),
    db: Session = Depends(get_db)
):
    """
    Geospatial partner lookup prioritizing scheme authorization, statutory compliance, and proximity.
    """
    return GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        max_npa=max_npa,
        partner_type=partner_type,
        partner_category=partner_category,
        district=district,
        state=state,
        pincode=pincode,
        scheme_id=scheme_id,
        loan_category=loan_category,
        service_type=service_type,
        limit=limit,
        include_excluded=include_excluded
    )


@router.get(
    "/directory",
    response_model=List[NearestPartnerResponse],
    status_code=status.HTTP_200_OK,
    summary="Browse channel partners directory",
    description="Returns active partners filtered by scheme, district, or category without requiring user coordinates."
)
def browse_partner_directory(
    district: Optional[str] = Query(None, description="Filter by district"),
    state: Optional[str] = Query(None, description="Filter by state"),
    partner_category: Optional[str] = Query(None, description="Filter by category"),
    scheme_id: Optional[str] = Query(None, description="Filter by scheme"),
    limit: int = Query(100, ge=1, le=200, description="Max results"),
    db: Session = Depends(get_db)
):
    """
    Browse partner directory with fallback origin.
    """
    # Default origin center (India central or UP)
    default_lat = 26.7606 if district and "gorakhpur" in district.lower() else 28.6139
    default_lng = 83.3732 if district and "gorakhpur" in district.lower() else 77.2090
    return GeoPartnerLocatorService.find_nearest_partners(
        db=db,
        latitude=default_lat,
        longitude=default_lng,
        radius_km=5000.0,
        max_npa=100.0,
        district=district,
        state=state,
        partner_category=partner_category,
        scheme_id=scheme_id,
        limit=limit
    )


@router.get(
    "/financial-health/schemes",
    response_model=List[SchemeFinancialSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List schemes with verified channel partner financial health coverage",
    description="Returns audited scheme counts with channel partners, verified financial indicators, and limited data counts from real database records."
)
def get_financial_health_schemes(
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Max schemes (omit for all canonical schemes)"),
    search: Optional[str] = Query(None, description="Search by scheme name or ID"),
    ministry: Optional[str] = Query(None, description="Filter by ministry"),
    has_partners_only: bool = Query(False, description="Include only schemes with mapped channel partners"),
    availability: Optional[str] = Query(None, description="Filter by availability: ALL, VERIFIED, LIMITED, DIRECT, FINANCIAL_ONLY"),
    db: Session = Depends(get_db)
):
    return ChannelPartnerEnrichmentService.get_financial_health_schemes(
        db=db,
        limit=limit,
        search=search,
        ministry=ministry,
        has_partners_only=has_partners_only,
        availability=availability
    )


@router.get(
    "/financial-health/schemes/{scheme_id}",
    response_model=SchemeFinancialDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get channel partner financial health directory for a specific scheme",
    description="Returns scheme financial summary and channel partners with neutral alphabetical ordering. Excludes quarantined partner records."
)
def get_scheme_financial_health(
    scheme_id: str = Path(..., description="Scheme ID"),
    search: Optional[str] = Query(None, description="Search partner name or code"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    partner_type: Optional[str] = Query(None, description="Filter by partner type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by financial status (STRONGER, MIXED, HIGHER_STRESS, LIMITED_DATA)"),
    db: Session = Depends(get_db)
):
    result = ChannelPartnerEnrichmentService.get_scheme_financial_health(
        db=db,
        scheme_id=scheme_id,
        search=search,
        state=state,
        district=district,
        partner_type=partner_type,
        status=status_filter
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme '{scheme_id}' not found or has no active channel partners"
        )
    return result


@router.get(
    "/{partner_id}/financial-health",
    response_model=PartnerFinancialHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get statutory financial intelligence and prudential evaluation for a channel partner",
    description="Returns multi-dimensional financial metrics, regulatory source citations, and NSFDC prudential rule evaluation."
)
@router.get(
    "/financial-health/{partner_id}",
    response_model=PartnerFinancialHealthResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def get_partner_financial_health(
    partner_id: str = Path(..., description="Unique Channel Partner ID"),
    db: Session = Depends(get_db)
):
    """
    Returns evidence-backed financial observations and statutory prudential evaluation.
    """
    result = GeoPartnerLocatorService.evaluate_partner_financial_health(db, partner_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel partner '{partner_id}' not found"
        )
    if result.get("record_status") == "QUARANTINED":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel partner '{partner_id}' has been quarantined per data integrity policy"
        )
    return result


@router.get(
    "/applications",
    response_model=PaginatedPartnerApplicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List applications for partner review",
    description="Returns a paginated list of submitted applications accessible to the authenticated partner or admin user. Enforces server-side partner isolation."
)
def list_partner_applications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by application status (e.g. SUBMITTED, UNDER_REVIEW)"),
    partner_id: Optional[str] = Query(None, description="Filter by assigned partner ID (SYSTEM_ADMIN only)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    """
    Lists applications for review with partner data isolation and status filtering.
    """
    return PartnerService.list_partner_applications(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        partner_id_filter=partner_id,
        page=page,
        page_size=page_size
    )


@router.get(
    "/applications/{application_id}",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get partner review details for an application",
    description="Returns full application detail for review including beneficiary profile, eligibility snapshot, uploaded documents, verification status, review notes, and audit history."
)
def get_partner_application_detail(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    """
    Retrieves full review details for a specific application. Enforces server-side partner data isolation.
    """
    return PartnerService.get_partner_application_detail(db, application_id, current_user)


@router.post(
    "/applications/{application_id}/assign",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign application to partner/reviewer",
    description="Assigns or reassigns an application to a target partner organization or reviewer user."
)
def assign_application(
    req: ApplicationAssignmentRequest,
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    """
    Assigns or reassigns application to a partner organization or reviewer user.
    """
    return PartnerService.assign_application(db, application_id, current_user, req)


@router.post(
    "/applications/{application_id}/start-review",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Initiate application review",
    description="Transitions application status from SUBMITTED to UNDER_REVIEW and records reviewer assignment."
)
def start_application_review(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    """
    Transitions state SUBMITTED -> UNDER_REVIEW.
    """
    return PartnerService.start_review(db, application_id, current_user)


@router.post(
    "/applications/{application_id}/documents/{app_document_id}/verify",
    response_model=DocumentReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify application document",
    description="Sets document verification status to VERIFIED, REJECTED, or NEEDS_CORRECTION with mandatory reason for rejection/correction."
)
def verify_application_document(
    req: DocumentReviewRequest,
    application_id: str = Path(..., description="Application UUID"),
    app_document_id: str = Path(..., description="Application Document UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return PartnerService.review_document(db, application_id, app_document_id, current_user, req)


@router.post(
    "/applications/{application_id}/documents/{app_document_id}/review",
    response_model=DocumentReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Review application document (Alias)",
    description="Alias for document verification endpoint."
)
def review_application_document(
    req: DocumentReviewRequest,
    application_id: str = Path(..., description="Application UUID"),
    app_document_id: str = Path(..., description="Application Document UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return PartnerService.review_document(db, application_id, app_document_id, current_user, req)


@router.post(
    "/applications/{application_id}/request-correction",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Request application correction",
    description="Transitions application status from UNDER_REVIEW to CORRECTION_REQUIRED with reason and target fields."
)
def request_application_correction(
    req: RequestCorrectionRequest,
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return PartnerService.request_correction(
        db=db,
        application_id=application_id,
        current_user=current_user,
        reason=req.reason,
        correction_fields=req.correction_fields
    )


@router.post(
    "/applications/{application_id}/approve",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve application",
    description="Transitions application status to APPROVED. Requires all mandatory documents to be VERIFIED."
)
def approve_application(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    req = ApplicationReviewDecisionRequest(decision="APPROVED", reason="Approved by authorized processing officer.")
    return PartnerService.process_review_decision(db, application_id, current_user, req)


@router.post(
    "/applications/{application_id}/reject",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject application",
    description="Transitions application status to REJECTED with mandatory rejection reason."
)
def reject_application(
    req: ApplicationReviewDecisionRequest,
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    req.decision = "REJECTED"
    return PartnerService.process_review_decision(db, application_id, current_user, req)


@router.post(
    "/applications/{application_id}/notes",
    response_model=ApplicationReviewNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add internal partner review note",
    description="Appends an internal review note to the application."
)
def add_application_review_note(
    req: ApplicationReviewNoteCreateRequest,
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return PartnerService.add_review_note(db, application_id, current_user, req)


@router.get(
    "/applications/{application_id}/approval-readiness",
    response_model=ApprovalReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check approval readiness",
    description="Verifies whether all mandatory scheme documents have been uploaded and verified prior to issuing an approval decision."
)
def check_approval_readiness(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_USER, UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return PartnerService.check_approval_readiness(db, application_id, current_user)


@router.post(
    "/applications/{application_id}/review",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue final review decision (APPROVED or REJECTED)",
    description="Issues final approval or rejection decision. Requires PARTNER_ADMIN or SYSTEM_ADMIN role. Approval requires all mandatory documents to be VERIFIED."
)
def process_review_decision(
    req: ApplicationReviewDecisionRequest,
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return PartnerService.process_review_decision(db, application_id, current_user, req)


@router.post(
    "/applications/{application_id}/complete",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark application completed / benefit disbursed",
    description="Transitions application status from APPROVED to COMPLETED."
)
def complete_application(
    application_id: str = Path(..., description="Application UUID"),
    notes: Optional[str] = Query(None, description="Optional completion notes or disbursement reference"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PARTNER_ADMIN, UserRole.SYSTEM_ADMIN))
):
    return PartnerService.complete_application(db, application_id, current_user, notes)

