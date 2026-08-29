import math
import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models.application import (
    Application,
    ApplicationDocument,
    ApplicationStatusHistory,
    ApplicationReviewNote,
    ApplicationStatus,
    DocumentVerificationStatus,
)
from app.models.partner import Partner
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.events.notifications import NotificationPublisher, NotificationEventType
from app.schemas.partner import (
    PartnerApplicationListItem,
    PaginatedPartnerApplicationListResponse,
    DocumentReviewRequest,
    DocumentReviewResponse,
    ApplicationAssignmentRequest,
    ApplicationReviewNoteCreateRequest,
    ApplicationReviewNoteResponse,
    ApplicationReviewDecisionRequest,
    ApprovalReadinessResponse,
    PartnerApplicationDetailResponse,
)

VALID_REVIEW_TRANSITIONS: Dict[str, set] = {
    ApplicationStatus.SUBMITTED.value: {
        ApplicationStatus.UNDER_REVIEW.value,
        ApplicationStatus.REJECTED.value,
    },
    ApplicationStatus.UNDER_REVIEW.value: {
        ApplicationStatus.APPROVED.value,
        ApplicationStatus.REJECTED.value,
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PartnerService:

    @classmethod
    def verify_partner_access(cls, application: Application, current_user: User) -> None:
        """
        Enforces partner data isolation:
        - SYSTEM_ADMIN has global access across all partners.
        - PARTNER_ADMIN and PARTNER_USER can only access applications assigned to their partner_id (or unassigned).
        - Accessing another partner's application returns HTTP 403 Forbidden.
        - BENEFICIARY access returns HTTP 403 Forbidden.
        """
        if current_user.role == UserRole.BENEFICIARY.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Beneficiaries are not authorized to access partner review endpoints."
            )

        if current_user.role == UserRole.SYSTEM_ADMIN.value:
            return

        # Partner users/admins must belong to a partner organization
        if not current_user.partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Partner account is not associated with an active partner organization."
            )

        # If application has an assigned_partner_id, it must match the current_user.partner_id
        if application.assigned_partner_id and application.assigned_partner_id != current_user.partner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Partner isolation restriction: You are not authorized to access applications assigned to another partner organization."
            )

    @classmethod
    def list_partner_applications(
        cls,
        db: Session,
        current_user: User,
        status_filter: Optional[str] = None,
        partner_id_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedPartnerApplicationListResponse:
        """
        Lists submitted/reviewable applications accessible to the partner/admin user.
        Enforces partner data isolation.
        """
        if current_user.role == UserRole.BENEFICIARY.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Beneficiaries cannot access partner application lists."
            )

        query = db.query(Application).options(
            selectinload(Application.scheme),
        )

        # Beneficiaries cannot see draft applications in partner list
        query = query.filter(Application.status.in_([
            ApplicationStatus.SUBMITTED.value,
            ApplicationStatus.UNDER_REVIEW.value,
            ApplicationStatus.APPROVED.value,
            ApplicationStatus.REJECTED.value,
        ]))

        # Enforce Partner Isolation
        if current_user.role != UserRole.SYSTEM_ADMIN.value:
            if not current_user.partner_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Partner account is not assigned to an organization."
                )
            # Filter applications assigned to this partner or unassigned
            query = query.filter(
                (Application.assigned_partner_id == current_user.partner_id) | (Application.assigned_partner_id.is_(None))
            )
        elif partner_id_filter:
            query = query.filter(Application.assigned_partner_id == partner_id_filter)

        if status_filter and status_filter.strip():
            query = query.filter(Application.status == status_filter.strip().upper())

        total = query.count()
        query = query.order_by(Application.submitted_at.desc(), Application.created_at.desc())

        pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return PaginatedPartnerApplicationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )

    @classmethod
    def get_partner_application_detail(
        cls,
        db: Session,
        application_id: str,
        current_user: User
    ) -> PartnerApplicationDetailResponse:
        """
        Retrieves full application details for review and enforces partner data isolation.
        """
        app_obj = db.query(Application).options(
            selectinload(Application.documents),
            selectinload(Application.status_history),
            selectinload(Application.review_notes),
            selectinload(Application.scheme),
        ).filter(Application.application_id == application_id).first()

        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)
        return app_obj

    @classmethod
    def assign_application(
        cls,
        db: Session,
        application_id: str,
        current_user: User,
        req: ApplicationAssignmentRequest
    ) -> PartnerApplicationDetailResponse:
        """
        Assigns or reassigns an application to a partner organization and/or reviewer user.
        Requires PARTNER_ADMIN or SYSTEM_ADMIN.
        """
        if current_user.role not in (UserRole.PARTNER_ADMIN.value, UserRole.SYSTEM_ADMIN.value, UserRole.PARTNER_USER.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to assign applications."
            )

        app_obj = db.query(Application).filter(Application.application_id == application_id).first()
        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)

        if req.partner_id:
            partner = db.query(Partner).filter(Partner.partner_id == req.partner_id).first()
            if not partner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Partner organization with ID '{req.partner_id}' was not found."
                )
            app_obj.assigned_partner_id = req.partner_id

        if req.reviewer_id:
            reviewer = db.query(User).filter(User.user_id == req.reviewer_id).first()
            if not reviewer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Reviewer user with ID '{req.reviewer_id}' was not found."
                )
            app_obj.assigned_reviewer_id = req.reviewer_id

        app_obj.updated_at = utc_now()

        # Audit note
        note = ApplicationReviewNote(
            application_id=application_id,
            author_id=current_user.user_id,
            author_role=current_user.role,
            content=f"Application assigned to partner '{req.partner_id or app_obj.assigned_partner_id}' / reviewer '{req.reviewer_id or app_obj.assigned_reviewer_id}'."
        )
        db.add(note)

        db.commit()

        if req.reviewer_id:
            NotificationPublisher.publish(
                db=db,
                event_type=NotificationEventType.APPLICATION_ASSIGNED,
                application_id=application_id,
                recipient_user_id=req.reviewer_id,
                scheme_name=app_obj.scheme.scheme_name if app_obj.scheme else "",
                payload={"assigned_by": current_user.user_id}
            )
            db.commit()

        return cls.get_partner_application_detail(db, application_id, current_user)

    @classmethod
    def start_review(
        cls,
        db: Session,
        application_id: str,
        current_user: User
    ) -> PartnerApplicationDetailResponse:
        """
        Transitions application from SUBMITTED -> UNDER_REVIEW when review begins.
        """
        app_obj = db.query(Application).filter(Application.application_id == application_id).first()
        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)

        if app_obj.status != ApplicationStatus.SUBMITTED.value:
            if app_obj.status == ApplicationStatus.UNDER_REVIEW.value:
                return cls.get_partner_application_detail(db, application_id, current_user)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot start review for application in status '{app_obj.status}'. Must be SUBMITTED."
            )

        old_status = app_obj.status
        new_status = ApplicationStatus.UNDER_REVIEW.value
        now = utc_now()

        app_obj.status = new_status
        app_obj.updated_at = now
        if not app_obj.assigned_reviewer_id:
            app_obj.assigned_reviewer_id = current_user.user_id
        if not app_obj.assigned_partner_id and current_user.partner_id:
            app_obj.assigned_partner_id = current_user.partner_id

        history = ApplicationStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.user_id,
            reason="Partner initiated application review."
        )
        db.add(history)

        db.commit()

        NotificationPublisher.publish(
            db=db,
            event_type=NotificationEventType.APPLICATION_UNDER_REVIEW,
            application_id=application_id,
            recipient_user_id=app_obj.user_id,
            scheme_name=app_obj.scheme.scheme_name if app_obj.scheme else "",
            payload={"reviewer_id": current_user.user_id}
        )
        db.commit()

        return cls.get_partner_application_detail(db, application_id, current_user)

    @classmethod
    def review_document(
        cls,
        db: Session,
        application_id: str,
        app_document_id: str,
        current_user: User,
        req: DocumentReviewRequest
    ) -> DocumentReviewResponse:
        """
        Reviews an uploaded application document, setting verification_status to VERIFIED or REJECTED.
        If REJECTED, reason is mandatory.
        """
        app_obj = db.query(Application).filter(Application.application_id == application_id).first()
        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)

        app_doc = db.query(ApplicationDocument).filter(
            ApplicationDocument.app_document_id == app_document_id,
            ApplicationDocument.application_id == application_id
        ).first()

        if not app_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application document with ID '{app_document_id}' was not found."
            )

        status_upper = req.verification_status.strip().upper()
        allowed_statuses = (
            DocumentVerificationStatus.VERIFIED.value,
            DocumentVerificationStatus.REJECTED.value,
            DocumentVerificationStatus.NEEDS_CORRECTION.value,
        )
        if status_upper not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"verification_status must be one of {allowed_statuses}."
            )

        if status_upper in (DocumentVerificationStatus.REJECTED.value, DocumentVerificationStatus.NEEDS_CORRECTION.value) and not (req.reason and req.reason.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A detailed reason is required when rejecting or requesting correction for a document."
            )

        now = utc_now()
        old_status = app_doc.verification_status
        app_doc.verification_status = status_upper
        app_doc.rejection_reason = req.reason.strip() if req.reason else None
        app_doc.verified_by = current_user.user_id
        app_doc.verified_at = now

        # Add audit log
        audit = AuditLog(
            actor_user_id=current_user.user_id,
            actor_role=current_user.role,
            application_id=application_id,
            action="VERIFY_DOCUMENT",
            old_value=old_status,
            new_value=status_upper,
            reason=req.reason.strip() if req.reason else f"Document {app_doc.document_name} status updated to {status_upper}"
        )
        db.add(audit)
        db.commit()

        if status_upper in (DocumentVerificationStatus.REJECTED.value, DocumentVerificationStatus.NEEDS_CORRECTION.value):
            NotificationPublisher.publish(
                db=db,
                event_type=NotificationEventType.DOCUMENT_REJECTED,
                application_id=application_id,
                recipient_user_id=app_obj.user_id,
                scheme_name=app_obj.scheme.scheme_name if app_obj.scheme else "",
                payload={"document_name": app_doc.document_name, "reason": req.reason}
            )
            db.commit()
        elif status_upper == DocumentVerificationStatus.VERIFIED.value:
            NotificationPublisher.publish(
                db=db,
                event_type=NotificationEventType.DOCUMENT_VERIFIED,
                application_id=application_id,
                recipient_user_id=app_obj.user_id,
                scheme_name=app_obj.scheme.scheme_name if app_obj.scheme else "",
                payload={"document_name": app_doc.document_name}
            )
            db.commit()

        return DocumentReviewResponse(
            app_document_id=app_document_id,
            application_id=application_id,
            document_name=app_doc.document_name,
            verification_status=status_upper,
            rejection_reason=app_doc.rejection_reason,
            verified_by=current_user.user_id,
            verified_at=now,
            message=f"Document '{app_doc.document_name}' verification status set to '{status_upper}'."
        )

    @classmethod
    def request_correction(
        cls,
        db: Session,
        application_id: str,
        current_user: User,
        reason: str,
        correction_fields: Optional[List[str]] = None
    ) -> PartnerApplicationDetailResponse:
        """
        Transitions application status UNDER_REVIEW -> CORRECTION_REQUIRED.
        Records correction reason, correction fields, status history, and audit log.
        """
        app_obj = db.query(Application).filter(Application.application_id == application_id).first()
        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)

        if app_obj.status not in (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot request correction for application in status '{app_obj.status}'. Must be SUBMITTED or UNDER_REVIEW."
            )

        old_status = app_obj.status
        new_status = ApplicationStatus.CORRECTION_REQUIRED.value
        now = utc_now()

        app_obj.status = new_status
        app_obj.correction_reason = reason.strip()
        app_obj.correction_fields = json.dumps(correction_fields or [])
        app_obj.updated_at = now

        history = ApplicationStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.user_id,
            reason=f"Correction requested: {reason.strip()}"
        )
        db.add(history)

        audit = AuditLog(
            actor_user_id=current_user.user_id,
            actor_role=current_user.role,
            application_id=application_id,
            action="REQUEST_CORRECTION",
            old_value=old_status,
            new_value=new_status,
            reason=reason.strip()
        )
        db.add(audit)

        db.commit()

        NotificationPublisher.publish(
            db=db,
            event_type=NotificationEventType.CORRECTION_REQUIRED,
            application_id=application_id,
            recipient_user_id=app_obj.user_id,
            scheme_name=app_obj.scheme.scheme_name if app_obj.scheme else "",
            payload={"reason": reason.strip(), "fields": correction_fields or []}
        )
        db.commit()

        return cls.get_partner_application_detail(db, application_id, current_user)

    @classmethod
    def add_review_note(
        cls,
        db: Session,
        application_id: str,
        current_user: User,
        req: ApplicationReviewNoteCreateRequest
    ) -> ApplicationReviewNoteResponse:
        """
        Appends an internal partner review note to the application.
        """
        app_obj = db.query(Application).filter(Application.application_id == application_id).first()
        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)

        note = ApplicationReviewNote(
            application_id=application_id,
            author_id=current_user.user_id,
            author_role=current_user.role,
            content=req.content.strip()
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        return note

    @classmethod
    def check_approval_readiness(
        cls,
        db: Session,
        application_id: str,
        current_user: User
    ) -> ApprovalReadinessResponse:
        """
        Checks whether mandatory documents are uploaded and verified before approval.
        """
        app_obj = db.query(Application).filter(Application.application_id == application_id).first()
        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)

        docs = db.query(ApplicationDocument).filter(
            ApplicationDocument.application_id == application_id
        ).all()

        blocking: List[str] = []

        for d in docs:
            if d.requirement_type == "REQUIRED":
                if not d.is_uploaded:
                    blocking.append(f"{d.document_name} (Not Uploaded)")
                elif d.verification_status != DocumentVerificationStatus.VERIFIED.value:
                    blocking.append(f"{d.document_name} (Status: {d.verification_status})")

        can_approve = (len(blocking) == 0) and (app_obj.status in (ApplicationStatus.SUBMITTED.value, ApplicationStatus.UNDER_REVIEW.value))

        msg = "Application is ready for approval." if can_approve else f"Approval blocked: {len(blocking)} mandatory document requirement(s) incomplete."

        return ApprovalReadinessResponse(
            application_id=application_id,
            status=app_obj.status,
            can_approve=can_approve,
            blocking_documents=blocking,
            message=msg
        )

    @classmethod
    def process_review_decision(
        cls,
        db: Session,
        application_id: str,
        current_user: User,
        req: ApplicationReviewDecisionRequest
    ) -> PartnerApplicationDetailResponse:
        """
        Processes final application approval or rejection decision:
        1. Validates user role authorization (PARTNER_ADMIN or SYSTEM_ADMIN)
        2. Validates current application state (SUBMITTED or UNDER_REVIEW)
        3. If APPROVED: verifies all mandatory documents are VERIFIED
        4. If REJECTED: verifies rejection reason is provided
        5. Performs atomic state transition and appends status history log
        """
        # Role authorization check: only PARTNER_ADMIN and SYSTEM_ADMIN can issue final decision
        if current_user.role not in (UserRole.PARTNER_ADMIN.value, UserRole.SYSTEM_ADMIN.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{current_user.role}' is not authorized to issue final approval/rejection decisions. Required role: PARTNER_ADMIN or SYSTEM_ADMIN."
            )

        app_obj = db.query(Application).filter(Application.application_id == application_id).first()
        if not app_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application with ID '{application_id}' was not found."
            )

        cls.verify_partner_access(app_obj, current_user)

        decision_upper = req.decision.strip().upper()
        if decision_upper not in (ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review decision must be either 'APPROVED' or 'REJECTED'."
            )

        if app_obj.status in (ApplicationStatus.APPROVED.value, ApplicationStatus.REJECTED.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Application has already been finalized in status '{app_obj.status}'."
            )

        if decision_upper == ApplicationStatus.APPROVED.value:
            readiness = cls.check_approval_readiness(db, application_id, current_user)
            if not readiness.can_approve:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot approve application: mandatory documents are not fully verified ({readiness.blocking_documents})."
                )

        if decision_upper == ApplicationStatus.REJECTED.value and not (req.reason and req.reason.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A detailed rejection reason is required when rejecting an application."
            )

        old_status = app_obj.status
        now = utc_now()

        app_obj.status = decision_upper
        app_obj.updated_at = now
        app_obj.assigned_reviewer_id = current_user.user_id
        app_obj.decision_at = now
        app_obj.decision_by = current_user.user_id

        if decision_upper == ApplicationStatus.REJECTED.value and req.reason:
            app_obj.rejection_reason = req.reason.strip()

        history = ApplicationStatusHistory(
            application_id=application_id,
            old_status=old_status,
            new_status=decision_upper,
            changed_by=current_user.user_id,
            reason=req.reason.strip() if req.reason else f"Application {decision_upper.lower()} by authorized reviewer."
        )
        db.add(history)

        audit = AuditLog(
            actor_user_id=current_user.user_id,
            actor_role=current_user.role,
            application_id=application_id,
            action=f"DECISION_{decision_upper}",
            old_value=old_status,
            new_value=decision_upper,
            reason=req.reason.strip() if req.reason else None
        )
        db.add(audit)

        db.commit()

        event_type = NotificationEventType.APPLICATION_APPROVED if decision_upper == ApplicationStatus.APPROVED.value else NotificationEventType.APPLICATION_REJECTED
        NotificationPublisher.publish(
            db=db,
            event_type=event_type,
            application_id=application_id,
            recipient_user_id=app_obj.user_id,
            scheme_name=app_obj.scheme.scheme_name if app_obj.scheme else "",
            payload={"decision": decision_upper, "reason": req.reason}
        )
        db.commit()

        return cls.get_partner_application_detail(db, application_id, current_user)
