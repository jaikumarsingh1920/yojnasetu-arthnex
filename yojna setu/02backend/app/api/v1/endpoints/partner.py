from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.partner import (
    PaginatedPartnerApplicationListResponse,
    PartnerApplicationDetailResponse,
    DocumentReviewRequest,
    DocumentReviewResponse,
    ApplicationAssignmentRequest,
    ApplicationReviewNoteCreateRequest,
    ApplicationReviewNoteResponse,
    ApplicationReviewDecisionRequest,
    ApprovalReadinessResponse,
    RequestCorrectionRequest,
)
from app.services.partner_service import PartnerService

router = APIRouter()


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
