import os
import json
import math
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.models.application import (
    Application,
    ApplicationDocument,
    ApplicationStatusHistory,
    ApplicationStatus,
    DocumentVerificationStatus,
)
from app.models.scheme import Scheme
from app.models.document import SchemeDocument
from app.models.user import User, UserRole
from app.models.partner import Partner
from app.schemas.profile import BeneficiaryProfileInput
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
    ApplicationResponse,
    PaginatedApplicationListResponse,
    SubmissionValidationResponse,
    DocumentUploadResponse,
)
from app.engine.eligibility import DeterministicEligibilityEngine

# Application State Machine valid transitions dictionary
VALID_TRANSITIONS: Dict[str, set] = {
    ApplicationStatus.DRAFT.value: {
        ApplicationStatus.DOCUMENTS_PENDING.value,
        ApplicationStatus.READY_FOR_SUBMISSION.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.DOCUMENTS_PENDING.value: {
        ApplicationStatus.READY_FOR_SUBMISSION.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.READY_FOR_SUBMISSION.value: {
        ApplicationStatus.SUBMITTED.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.SUBMITTED.value: {
        ApplicationStatus.UNDER_REVIEW.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.UNDER_REVIEW.value: {
        ApplicationStatus.APPROVED.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.CORRECTION_REQUIRED.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.CORRECTION_REQUIRED.value: {
        ApplicationStatus.DOCUMENTS_PENDING.value,
        ApplicationStatus.READY_FOR_SUBMISSION.value,
        ApplicationStatus.SUBMITTED.value,
        ApplicationStatus.WITHDRAWN.value,
    },
    ApplicationStatus.APPROVED.value: {
        ApplicationStatus.COMPLETED.value,
    },
    ApplicationStatus.REJECTED.value: set(),
    ApplicationStatus.WITHDRAWN.value: set(),
    ApplicationStatus.COMPLETED.value: set(),
}

ACTIVE_STATUSES = {
    ApplicationStatus.DRAFT.value,
    ApplicationStatus.DOCUMENTS_PENDING.value,
    ApplicationStatus.READY_FOR_SUBMISSION.value,
    ApplicationStatus.SUBMITTED.value,
    ApplicationStatus.UNDER_REVIEW.value,
    ApplicationStatus.CORRECTION_REQUIRED.value,
}

# Prototype storage directory for document uploads
UPLOAD_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads", "applications")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApplicationService:

    @classmethod
    def validate_transition(cls, current_status: str, target_status: str) -> None:
        """
        Enforces strict state machine transition rules.
        Raises HTTPException 400 if transition is illegal.
        """
        allowed = VALID_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Illegal application status transition from '{current_status}' to '{target_status}'. Allowed target status(es): {sorted(list(allowed))}"
            )

    @classmethod
    def verify_ownership(cls, application: Application, current_user: User) -> None:
        """
        Enforces server-side ownership: user can only access/modify their own applications.
        SYSTEM_ADMIN bypasses ownership.
        """
        if application.user_id != current_user.user_id and current_user.role != UserRole.SYSTEM_ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access or modify another user's application."
            )

    @classmethod
    def create_application(
        cls,
        db: Session,
        current_user: User,
        req: ApplicationCreateRequest
    ) -> Application:
        """
        1. Authenticate user and verify role
        2. Verify scheme exists in DB
        3. Check duplicate active application rule
        4. Evaluate eligibility using DeterministicEligibilityEngine (TASK-003)
        5. Create Application record with profile & eligibility snapshots
        6. Initialize ApplicationDocument tracking records from master SchemeDocument data
        7. Transition initial status (DOCUMENTS_PENDING vs READY_FOR_SUBMISSION)
        8. Append initial ApplicationStatusHistory record
        """
        # 1. Verify scheme exists
        scheme = db.query(Scheme).options(
            selectinload(Scheme.documents),
            selectinload(Scheme.rules),
            selectinload(Scheme.verifications),
        ).filter(Scheme.scheme_id == req.scheme_id).first()

        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scheme with ID '{req.scheme_id}' was not found in the database."
            )

        # 2. Check for existing active application for (user_id, scheme_id)
        existing_active = db.query(Application).filter(
            Application.user_id == current_user.user_id,
            Application.scheme_id == req.scheme_id,
            Application.status.in_(ACTIVE_STATUSES)
        ).first()

        if existing_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An active application already exists for scheme '{req.scheme_id}' in status '{existing_active.status}' (Application ID: {existing_active.application_id}). Please track or complete your existing application."
            )

        # 3. Evaluate eligibility via TASK-003 DeterministicEligibilityEngine
        elig_res = DeterministicEligibilityEngine.evaluate_scheme(scheme, req.profile)

        profile_dump = req.profile.model_dump()
        elig_dump = elig_res.model_dump()

        # 4. Create application
        application = Application(
            user_id=current_user.user_id,
            scheme_id=req.scheme_id,
            status=ApplicationStatus.DRAFT.value,
            profile_snapshot=json.dumps(profile_dump),
            eligibility_snapshot=json.dumps(elig_dump),
        )
        db.add(application)
        db.flush()  # Generate application_id

        # 5. Initialize application document tracking from master SchemeDocument records
        master_docs = scheme.documents
        required_count = 0

        for m_doc in master_docs:
            if m_doc.active:
                req_type = m_doc.requirement_type or "REQUIRED"
                if req_type == "REQUIRED":
                    required_count += 1
                app_doc = ApplicationDocument(
                    application_id=application.application_id,
                    document_id=m_doc.document_id,
                    document_name=m_doc.document_name,
                    requirement_type=req_type,
                    condition=m_doc.condition,
                    is_uploaded=False,
                    verification_status=DocumentVerificationStatus.PENDING.value,
                )
                db.add(app_doc)

        # 6. Determine initial status
        initial_status = ApplicationStatus.DOCUMENTS_PENDING.value if required_count > 0 else ApplicationStatus.READY_FOR_SUBMISSION.value
        old_status = application.status
        application.status = initial_status

        # 7. Add initial status history record
        history = ApplicationStatusHistory(
            application_id=application.application_id,
            old_status=old_status,
            new_status=initial_status,
            changed_by=current_user.user_id,
            reason=f"Application created for scheme '{scheme.scheme_name}'."
        )
        db.add(history)

        db.commit()

        # Re-query with pre-loaded relations
        return cls.get_application_by_id(db, application.application_id, current_user)

    @classmethod
    def get_application_by_id(
        cls,
        db: Session,
        application_id: str,
        current_user: User
    ) -> Application:
        """
        Retrieves an application by ID with pre-loaded relations and enforces server-side ownership.
        """
        app_obj = db.query(Application).options(
            selectinload(Application.documents),
            selectinload(Application.status_history),
            selectinload(Application.scheme),
        ).filter(Application.application_id == application_id).first()

        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_ownership(app_obj, current_user)
        return app_obj

    @classmethod
    def update_draft_application(
        cls,
        db: Session,
        application_id: str,
        current_user: User,
        req: ApplicationUpdateRequest
    ) -> Application:
        """
        Updates profile data for a DRAFT or DOCUMENTS_PENDING application.
        Re-evaluates eligibility snapshot. Blocked after submission.
        """
        app_obj = cls.get_application_by_id(db, application_id, current_user)

        if app_obj.status in (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot update application in status '{app_obj.status}'. Submitted applications are immutable."
            )

        scheme = db.query(Scheme).filter(Scheme.scheme_id == app_obj.scheme_id).first()

        # Re-evaluate eligibility
        elig_res = DeterministicEligibilityEngine.evaluate_scheme(scheme, req.profile)

        app_obj.profile_snapshot = json.dumps(req.profile.model_dump())
        app_obj.eligibility_snapshot = json.dumps(elig_res.model_dump())
        app_obj.updated_at = utc_now()

        db.commit()
        return cls.get_application_by_id(db, application_id, current_user)

    @classmethod
    def upload_document(
        cls,
        db: Session,
        application_id: str,
        app_document_id: str,
        current_user: User,
        file: UploadFile
    ) -> DocumentUploadResponse:
        """
        Prototype Document Upload Adapter:
        1. Verifies ownership and submittable application status
        2. Validates document record exists
        3. Saves uploaded file safely to local prototype storage directory
        4. Updates ApplicationDocument record
        5. Re-evaluates document completion; if all REQUIRED documents uploaded -> transitions status to READY_FOR_SUBMISSION
        """
        app_obj = cls.get_application_by_id(db, application_id, current_user)

        if app_obj.status in (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value, ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot upload documents for application in status '{app_obj.status}'."
            )

        app_doc = db.query(ApplicationDocument).filter(
            ApplicationDocument.app_document_id == app_document_id,
            ApplicationDocument.application_id == application_id
        ).first()

        if not app_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application document with ID '{app_document_id}' was not found for this application."
            )

        # File Hardening & Validation
        raw_filename = file.filename or "uploaded_document"
        original_filename = os.path.basename(raw_filename)
        _, ext = os.path.splitext(original_filename.lower())

        DANGEROUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".php", ".js", ".py", ".htm", ".html", ".dll", ".vbs", ".jar", ".msi", ".cpl", ".scr"}
        ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

        if ext in DANGEROUS_EXTENSIONS or (ext not in ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security error: File extension '{ext}' is not permitted. Only PDF, JPG, JPEG, and PNG files are accepted."
            )

        # Prototype File Storage Adapter & Path Traversal Boundary Check
        app_upload_dir = os.path.abspath(os.path.join(UPLOAD_BASE_DIR, application_id))
        os.makedirs(app_upload_dir, exist_ok=True)

        import uuid
        safe_filename = f"{app_document_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_dest_path = os.path.abspath(os.path.join(app_upload_dir, safe_filename))

        # Enforce Path Traversal Boundary
        if not file_dest_path.startswith(app_upload_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security error: Invalid target file path (Path traversal detected)."
            )

        # Read and check size limit (10 MB max)
        content = file.file.read()
        file_size = len(content)
        MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

        if file_size > MAX_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size} bytes) exceeds maximum allowable limit of 10MB."
            )

        with open(file_dest_path, "wb") as f:
            f.write(content)

        now = utc_now()
        app_doc.is_uploaded = True
        app_doc.file_path = file_dest_path
        app_doc.file_name = original_filename
        app_doc.file_size_bytes = file_size
        app_doc.mime_type = file.content_type
        app_doc.uploaded_at = now
        app_doc.verification_status = DocumentVerificationStatus.PENDING.value

        # Re-check document completion
        all_docs = db.query(ApplicationDocument).filter(
            ApplicationDocument.application_id == application_id
        ).all()

        missing_required = [d for d in all_docs if d.requirement_type == "REQUIRED" and not d.is_uploaded]

        # Transition status to READY_FOR_SUBMISSION if all REQUIRED docs uploaded
        if len(missing_required) == 0 and app_obj.status in (ApplicationStatus.DRAFT.value, ApplicationStatus.DOCUMENTS_PENDING.value):
            old_st = app_obj.status
            new_st = ApplicationStatus.READY_FOR_SUBMISSION.value
            app_obj.status = new_st
            app_obj.updated_at = now

            history = ApplicationStatusHistory(
                application_id=application_id,
                old_status=old_st,
                new_status=new_st,
                changed_by=current_user.user_id,
                reason="All mandatory documents uploaded; application ready for submission."
            )
            db.add(history)

        db.commit()

        return DocumentUploadResponse(
            app_document_id=app_document_id,
            application_id=application_id,
            is_uploaded=True,
            file_name=original_filename,
            file_size_bytes=file_size,
            mime_type=file.content_type,
            uploaded_at=now,
            application_status=app_obj.status,
            message=f"Document '{app_doc.document_name}' uploaded successfully."
        )

    @classmethod
    def validate_submission(
        cls,
        db: Session,
        application_id: str,
        current_user: User
    ) -> SubmissionValidationResponse:
        """
        Validates if an application is complete and ready for submission.
        Checks mandatory document status.
        """
        app_obj = cls.get_application_by_id(db, application_id, current_user)

        docs = db.query(ApplicationDocument).filter(
            ApplicationDocument.application_id == application_id
        ).all()

        missing_required_names = [
            d.document_name for d in docs if d.requirement_type == "REQUIRED" and not d.is_uploaded
        ]

        can_submit = (len(missing_required_names) == 0) and (app_obj.status in (
            ApplicationStatus.READY_FOR_SUBMISSION.value,
            ApplicationStatus.DOCUMENTS_PENDING.value,
            ApplicationStatus.DRAFT.value,
            ApplicationStatus.CORRECTION_REQUIRED.value
        ))

        msg = "Application is ready for submission." if can_submit else f"Cannot submit: missing {len(missing_required_names)} required document(s)."

        return SubmissionValidationResponse(
            application_id=application_id,
            status=app_obj.status,
            can_submit=can_submit,
            missing_documents=missing_required_names,
            message=msg
        )

    @classmethod
    def submit_application(
        cls,
        db: Session,
        application_id: str,
        current_user: User,
        partner_id: str
    ) -> Application:
        """
        Submits an application:
        1. Verify ownership and valid state
        2. Check mandatory documents
        3. Transition status to SUBMITTED
        4. Populate submitted_at timestamp
        5. Record status history atomically
        """
        app_obj = cls.get_application_by_id(db, application_id, current_user)

        if not partner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A valid Channel Partner must be selected to submit this application. Direct loans are not entertained."
            )

        partner = db.query(Partner).filter(
            Partner.partner_id == partner_id,
            Partner.is_active == True,
            Partner.is_accepting_applications == True
        ).first()

        if not partner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The selected partner is invalid, inactive, or not accepting applications."
            )

        if app_obj.status == ApplicationStatus.SUBMITTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application has already been submitted."
            )

        if app_obj.status in (ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit finalized application in status '{app_obj.status}'."
            )

        # Check mandatory documents
        val_res = cls.validate_submission(db, application_id, current_user)
        if not val_res.can_submit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit application: missing {len(val_res.missing_documents)} mandatory document(s): {val_res.missing_documents}"
            )

        old_status = app_obj.status
        new_status = ApplicationStatus.SUBMITTED.value
        cls.validate_transition(old_status, new_status)

        now = utc_now()
        app_obj.status = new_status
        app_obj.assigned_partner_id = partner_id
        app_obj.submitted_at = now
        app_obj.updated_at = now

        history = ApplicationStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.user_id,
            reason="Beneficiary submitted application."
        )
        db.add(history)

        db.commit()

        from app.events.notifications import NotificationPublisher, NotificationEventType

        scheme_name = app_obj.scheme.scheme_name if app_obj.scheme else ""
        event_enum = (
            NotificationEventType.APPLICATION_RESUBMITTED
            if old_status == ApplicationStatus.CORRECTION_REQUIRED.value
            else NotificationEventType.APPLICATION_SUBMITTED
        )

        # Notify beneficiary
        NotificationPublisher.publish(
            db=db,
            event_type=event_enum,
            application_id=application_id,
            recipient_user_id=current_user.user_id,
            scheme_name=scheme_name,
            payload={"submitted_at": now.isoformat(), "target_role": "BENEFICIARY"}
        )

        # Notify reviewer if assigned
        if app_obj.assigned_reviewer_id and app_obj.assigned_reviewer_id != current_user.user_id:
            NotificationPublisher.publish(
                db=db,
                event_type=event_enum,
                application_id=application_id,
                recipient_user_id=app_obj.assigned_reviewer_id,
                scheme_name=scheme_name,
                payload={"submitted_at": now.isoformat(), "target_role": "PARTNER_USER"}
            )

        db.commit()

        return cls.get_application_by_id(db, application_id, current_user)

    @classmethod
    def list_user_applications(
        cls,
        db: Session,
        current_user: User,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedApplicationListResponse:
        """
        Returns a paginated list of applications belonging ONLY to the authenticated beneficiary.
        """
        query = db.query(Application).options(
            selectinload(Application.documents),
            selectinload(Application.status_history),
            selectinload(Application.scheme),
        )

        # Enforce beneficiary data isolation: only query current user's applications
        if current_user.role != UserRole.SYSTEM_ADMIN.value:
            query = query.filter(Application.user_id == current_user.user_id)

        if status_filter and status_filter.strip():
            query = query.filter(Application.status == status_filter.strip().upper())

        total = query.count()
        query = query.order_by(Application.created_at.desc())

        pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return PaginatedApplicationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )

    @classmethod
    def withdraw_application(
        cls,
        db: Session,
        application_id: str,
        current_user: User,
        reason: Optional[str] = None
    ) -> Application:
        """
        Allows a beneficiary to withdraw their active application.
        Transitions state to WITHDRAWN and logs history & notifications.
        """
        app_obj = cls.get_application_by_id(db, application_id, current_user)

        if app_obj.status in (ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value, ApplicationStatus.WITHDRAWN.value, ApplicationStatus.COMPLETED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot withdraw application in finalized status '{app_obj.status}'."
            )

        old_status = app_obj.status
        new_status = ApplicationStatus.WITHDRAWN.value
        cls.validate_transition(old_status, new_status)

        now = utc_now()
        app_obj.status = new_status
        app_obj.updated_at = now

        withdraw_reason = reason.strip() if reason and reason.strip() else "Beneficiary withdrew application."

        history = ApplicationStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.user_id,
            reason=withdraw_reason
        )
        db.add(history)
        db.commit()

        from app.events.notifications import NotificationPublisher, NotificationEventType

        NotificationPublisher.publish(
            db=db,
            event_type=NotificationEventType.APPLICATION_WITHDRAWN,
            application_id=application_id,
            recipient_user_id=current_user.user_id,
            scheme_name=app_obj.scheme.scheme_name if app_obj.scheme else "",
            payload={"withdrawn_at": now.isoformat(), "reason": withdraw_reason}
        )
        db.commit()

        return cls.get_application_by_id(db, application_id, current_user)

