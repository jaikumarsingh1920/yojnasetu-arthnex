from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
    ApplicationResponse,
    PaginatedApplicationListResponse,
    SubmissionValidationResponse,
    DocumentUploadResponse,
)
from app.services.application_service import ApplicationService

router = APIRouter()


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new scheme application",
    description="Allows an authenticated beneficiary to select a scheme, evaluate eligibility snapshot, and create an application draft with document checklist."
)
def create_application(
    req: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.BENEFICIARY, UserRole.SYSTEM_ADMIN))
):
    """
    1. Authenticates beneficiary user.
    2. Verifies target scheme exists in database.
    3. Prevents duplicate active applications for the same scheme.
    4. Evaluates current eligibility snapshot via DeterministicEligibilityEngine.
    5. Initializes application document checklist from master scheme documents.
    6. Sets initial status (DOCUMENTS_PENDING or READY_FOR_SUBMISSION) and appends status history.
    """
    return ApplicationService.create_application(db, current_user, req)


@router.get(
    "",
    response_model=PaginatedApplicationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List beneficiary's applications",
    description="Returns a paginated list of applications belonging strictly to the authenticated beneficiary."
)
def list_my_applications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by application status (e.g. DRAFT, SUBMITTED)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns only applications belonging to the authenticated beneficiary.
    Supports filtering by status and pagination. Cross-user leakage is prevented server-side.
    """
    return ApplicationService.list_user_applications(
        db=db,
        current_user=current_user,
        status_filter=status_filter,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get application details",
    description="Returns full application details including profile snapshot, eligibility snapshot, document checklist, and status history."
)
def get_application_details(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves full details for a specific application. Enforces strict server-side ownership.
    """
    return ApplicationService.get_application_by_id(db, application_id, current_user)


@router.put(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update draft application profile",
    description="Allows updating the beneficiary profile snapshot for an unsubmitted application."
)
def update_draft_application(
    req: ApplicationUpdateRequest,
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates profile snapshot and re-evaluates eligibility for a draft/unsubmitted application.
    Submitted or finalized applications cannot be updated.
    """
    return ApplicationService.update_draft_application(db, application_id, current_user, req)


@router.post(
    "/{application_id}/documents/{app_document_id}/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload application document",
    description="Uploads a required or optional document file for an application."
)
def upload_application_document(
    application_id: str = Path(..., description="Application UUID"),
    app_document_id: str = Path(..., description="Application Document UUID"),
    file: UploadFile = File(..., description="Document file to upload"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a document file using the prototype storage adapter, updates the document tracking record,
    and transitions application status to READY_FOR_SUBMISSION when all mandatory documents are complete.
    """
    return ApplicationService.upload_document(db, application_id, app_document_id, current_user, file)


@router.get(
    "/{application_id}/validate",
    response_model=SubmissionValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate application readiness for submission",
    description="Checks whether mandatory document requirements are satisfied prior to submission."
)
def validate_application_submission(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns structured validation response indicating missing mandatory documents and submission eligibility.
    """
    return ApplicationService.validate_submission(db, application_id, current_user)


@router.post(
    "/{application_id}/submit",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit application",
    description="Submits the application, transitions status to SUBMITTED, populates submitted_at timestamp, and records status history."
)
def submit_application(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    1. Verifies ownership and submittable state.
    2. Validates that all mandatory scheme documents have been uploaded.
    3. Transitions state from READY_FOR_SUBMISSION -> SUBMITTED.
    4. Records submitted_at timestamp and appends status history atomically.
    """
    return ApplicationService.submit_application(db, application_id, current_user)
