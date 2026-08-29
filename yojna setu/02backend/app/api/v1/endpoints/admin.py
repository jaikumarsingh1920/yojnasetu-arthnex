from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.schemas.partner import PaginatedPartnerApplicationListResponse, PartnerApplicationDetailResponse, ApplicationAssignmentRequest, AdminStatsResponse
from app.schemas.admin import (
    AdminDashboardSummaryResponse,
    PaginatedSchemeAuditResponse,
    SchemeAuditDetailResponse,
    PaginatedRuleAuditResponse,
    PaginatedDocumentAuditResponse,
    PaginatedChangelogResponse,
    SystemHealthResponse,
)
from app.services.admin_service import AdminService
from app.services.partner_service import PartnerService

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=AdminDashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Admin Dashboard Summary",
    description="Returns global statistics across 56 schemes, 57 rules, 20 documents, application counts, notifications, and system health."
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
    summary="List all 56 schemes for audit",
    description="Returns audit table of all schemes with VERIFIED status badges, completeness scores, and rule/document counts."
)
def get_scheme_audit_list(
    search: Optional[str] = Query(None, description="Search by scheme ID, name, or ministry"),
    ministry: Optional[str] = Query(None, description="Filter by ministry"),
    sector: Optional[str] = Query(None, description="Filter by sector/type"),
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
        page=page,
        page_size=page_size
    )


@router.get(
    "/schemes/{scheme_id}",
    response_model=SchemeAuditDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get exhaustive scheme detail audit",
    description="Returns detailed parameter breakdown, rules, documents, changelogs, and data quality warnings."
)
def get_scheme_audit_detail(
    scheme_id: str = Path(..., description="Target scheme ID (e.g. SIH26092-052)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_scheme_audit_detail(db=db, current_user=current_user, scheme_id=scheme_id)


@router.get(
    "/rules",
    response_model=PaginatedRuleAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="List all 57 database rules",
    description="Returns audit table of all scheme eligibility and financial rules."
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
    summary="List all 20 document requirements",
    description="Returns audit table of all scheme document requirements."
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
    description="Returns history log of scheme enrichments and audit changes."
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
    description="Evaluates operational health of Database, RAG, AI Provider, and Deterministic Engines."
)
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_system_health(db=db)


@router.get(
    "/applications",
    response_model=PaginatedPartnerApplicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all applications (System Admin)",
    description="Returns global paginated list of all applications across all partners with filtering, search, and status distribution."
)
def list_admin_applications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by application status"),
    scheme_id: Optional[str] = Query(None, description="Filter by target scheme ID"),
    partner_id: Optional[str] = Query(None, description="Filter by assigned partner ID"),
    reviewer_id: Optional[str] = Query(None, description="Filter by assigned reviewer user ID"),
    search: Optional[str] = Query(None, description="Search term for application ID, user ID, or scheme ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_admin_applications(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        scheme_id_filter=scheme_id,
        partner_id_filter=partner_id,
        reviewer_id_filter=reviewer_id,
        search=search,
        page=page,
        page_size=page_size
    )


@router.get(
    "/applications/stats",
    response_model=AdminStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Admin application statistics",
    description="Returns aggregated metrics for total applications, status breakdown, pending document verifications, and scheme workload."
)
def get_admin_application_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return AdminService.get_admin_stats(db=db, current_user=current_user)


@router.post(
    "/applications/{application_id}/reassign",
    response_model=PartnerApplicationDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Reassign application (System Admin)",
    description="Reassigns an application to a target partner organization or reviewer user."
)
def reassign_admin_application(
    req: ApplicationAssignmentRequest,
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))
):
    return PartnerService.assign_application(db, application_id, current_user, req)
