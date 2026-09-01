from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminDashboardSummaryResponse,
    PaginatedSchemeAuditResponse,
    SchemeAuditDetailResponse,
    PaginatedRuleAuditResponse,
    PaginatedDocumentAuditResponse,
    PaginatedChangelogResponse,
    SystemHealthResponse,
    SchemeCreateInput,
    SchemeUpdateInput,
    SchemeStatusUpdateInput,
    PartnerAuditItem,
    PaginatedPartnerAuditResponse,
    PartnerCreateAdminInput,
    PartnerUpdateAdminInput,
    PartnerStatusAdminInput,
    PartnerMappingAdminInput,
)
from app.services.admin_service import AdminService

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=AdminDashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Admin Dashboard Governance Summary",
    description="Returns verified statistics across 90 schemes, 126 rules, 98 documents, data completeness, ministries, changelogs, and live system health."
)
def get_admin_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_dashboard_summary(db=db, current_user=current_user)


@router.get(
    "/schemes",
    response_model=PaginatedSchemeAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="List all schemes for audit and management",
    description="Returns audit table of all schemes with VERIFIED status badges, completeness scores, rule/document counts, and official source links."
)
def get_scheme_audit_list(
    search: Optional[str] = Query(None, description="Search by scheme ID, name, or ministry"),
    ministry: Optional[str] = Query(None, description="Filter by ministry"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE / INACTIVE)"),
    scheme_type: Optional[str] = Query(None, description="Filter by scheme type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_scheme_audit_list(
        db=db,
        current_user=current_user,
        search=search,
        ministry=ministry,
        sector=sector,
        status=status,
        scheme_type=scheme_type,
        page=page,
        page_size=page_size
    )


@router.post(
    "/schemes",
    response_model=SchemeAuditDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new canonical scheme with strict validation and audit logging",
    description="Registers a new verified scheme in the canonical database, validates all fields, and logs a creation entry in the audit changelog."
)
def create_scheme(
    data: SchemeCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.create_scheme(db=db, current_user=current_user, data=data)


@router.get(
    "/schemes/{scheme_id}",
    response_model=SchemeAuditDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get exhaustive scheme detail audit",
    description="Returns detailed parameter breakdown, rules, documents, changelogs, official source portal, and data quality warnings."
)
def get_scheme_audit_detail(
    scheme_id: str = Path(..., description="Target scheme ID (e.g. SIH26092-052)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_scheme_audit_detail(db=db, current_user=current_user, scheme_id=scheme_id)


@router.put(
    "/schemes/{scheme_id}",
    response_model=SchemeAuditDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update canonical scheme parameters",
    description="Updates existing canonical scheme record, validates changes, and records each changed field in the audit changelog."
)
def update_scheme(
    scheme_id: str = Path(..., description="Target scheme ID"),
    data: SchemeUpdateInput = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.update_scheme(db=db, current_user=current_user, scheme_id=scheme_id, data=data)


@router.patch(
    "/schemes/{scheme_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Activate or Deactivate scheme lifecycle status",
    description="Toggles scheme between ACTIVE and INACTIVE state. Deactivated schemes are immediately excluded from public directory, calculator, and recommendations."
)
def update_scheme_status(
    scheme_id: str = Path(..., description="Target scheme ID"),
    data: SchemeStatusUpdateInput = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.update_scheme_status(db=db, current_user=current_user, scheme_id=scheme_id, data=data)


@router.get(
    "/rules",
    response_model=PaginatedRuleAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="List all 126 database condition rules",
    description="Returns audit table of all deterministic scheme eligibility and financial rules."
)
def get_rule_audit_list(
    scheme_id: Optional[str] = Query(None, description="Filter by scheme ID"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_rule_audit_list(
        db=db,
        current_user=current_user,
        scheme_id=scheme_id,
        rule_type=rule_type,
        page=page,
        page_size=page_size
    )


@router.get(
    "/documents",
    response_model=PaginatedDocumentAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="List all 98 document requirements",
    description="Returns audit table of all verified scheme document requirements categorized by type."
)
def get_document_audit_list(
    scheme_id: Optional[str] = Query(None, description="Filter by scheme ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_document_audit_list(
        db=db,
        current_user=current_user,
        scheme_id=scheme_id,
        page=page,
        page_size=page_size
    )


@router.get(
    "/changelog",
    response_model=PaginatedChangelogResponse,
    status_code=status.HTTP_200_OK,
    summary="List scheme data changelog entries",
    description="Returns history log of 212 scheme enrichments, rule updates, and audit changes."
)
def get_scheme_changelog(
    scheme_id: Optional[str] = Query(None, description="Filter by scheme ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_scheme_changelog(
        db=db,
        current_user=current_user,
        scheme_id=scheme_id,
        page=page,
        page_size=page_size
    )


@router.get(
    "/system-health",
    response_model=SystemHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system & AI infrastructure health status",
    description="Evaluates operational health of Database, RAG Chunk Index, AI Provider, and Deterministic Engines."
)
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_system_health(db=db)


# =====================================================================
# PARTNER DIRECTORY MANAGEMENT ENDPOINTS
# =====================================================================

@router.get(
    "/partners",
    response_model=PaginatedPartnerAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="List all channel partners for governance",
    description="Returns paginated partner audit list with category, status, and mapped scheme counts."
)
def get_partner_audit_list(
    search: Optional[str] = Query(None, description="Search by name, code, partner ID, or district"),
    district: Optional[str] = Query(None, description="Filter by district"),
    state: Optional[str] = Query(None, description="Filter by state"),
    partner_category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE / INACTIVE)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_partner_audit_list(
        db=db,
        current_user=current_user,
        search=search,
        district=district,
        state=state,
        partner_category=partner_category,
        status_filter=status,
        page=page,
        page_size=page_size
    )


@router.post(
    "/partners",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new verified channel partner",
    description="Adds a new channel partner or assistance center with audit tracking."
)
def create_partner(
    data: PartnerCreateAdminInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.create_partner(db=db, current_user=current_user, data=data)


@router.put(
    "/partners/{partner_id}",
    status_code=status.HTTP_200_OK,
    summary="Update channel partner details",
    description="Updates partner details and records diff in partner changelog."
)
def update_partner(
    partner_id: str = Path(..., description="Partner ID"),
    data: PartnerUpdateAdminInput = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.update_partner(db=db, current_user=current_user, partner_id=partner_id, data=data)


@router.patch(
    "/partners/{partner_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Toggle partner active / inactive state",
    description="Soft-deactivates or reactivates partner with audit reason."
)
def update_partner_status(
    partner_id: str = Path(..., description="Partner ID"),
    data: PartnerStatusAdminInput = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.update_partner_status(db=db, current_user=current_user, partner_id=partner_id, data=data)


@router.post(
    "/partners/{partner_id}/schemes",
    status_code=status.HTTP_200_OK,
    summary="Link scheme mapping to partner",
    description="Establishes an explicit verified relationship between a partner and a scheme."
)
def add_partner_scheme_mapping(
    partner_id: str = Path(..., description="Partner ID"),
    data: PartnerMappingAdminInput = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.add_partner_scheme_mapping(db=db, current_user=current_user, partner_id=partner_id, data=data)


@router.delete(
    "/partners/{partner_id}/schemes/{scheme_id}",
    status_code=status.HTTP_200_OK,
    summary="Unlink scheme mapping from partner",
    description="Removes a scheme mapping with audit log."
)
def remove_partner_scheme_mapping(
    partner_id: str = Path(..., description="Partner ID"),
    scheme_id: str = Path(..., description="Scheme ID"),
    reason: Optional[str] = Query(None, description="Reason for removing mapping"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.remove_partner_scheme_mapping(
        db=db,
        current_user=current_user,
        partner_id=partner_id,
        scheme_id=scheme_id,
        reason=reason
    )

