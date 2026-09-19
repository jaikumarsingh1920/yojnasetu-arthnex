import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.scheme import Scheme
from app.models.changelog import SchemeChangelog
from app.models.ingestion import PendingSchemeUpdate, SchemeSource
from app.models.candidate import CandidateScheme
from app.models.user import User
from app.services.ingestion.sync_service import IngestionSyncService
from app.services.ingestion.promotion_service import CandidatePromotionService

logger = logging.getLogger("yojnasetu.ingestion.approval")


class PendingUpdateApprovalService:
    """
    Administrative Review and Approval Service for pending scheme updates.
    Enforces human-in-the-loop verification, immutable audit logging in SchemeChangelog,
    version bumping, and rule/RAG synchronization.
    Supports both instance-based and classmethod invocations.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def process_review(
        self,
        update_id: str,
        action: str,
        reviewer_id: Optional[str] = None,
        reason: Optional[str] = None,
        db: Optional[Session] = None
    ) -> PendingSchemeUpdate:
        target_db = db or self.db
        if not target_db:
            raise ValueError("Database session is required.")

        update = target_db.query(PendingSchemeUpdate).filter(PendingSchemeUpdate.update_id == update_id).first()
        if not update:
            raise ValueError(f"Pending update with ID '{update_id}' not found.")

        if update.status != "PENDING":
            raise ValueError(f"Update '{update_id}' has already been reviewed (Status: {update.status}).")

        admin_id = reviewer_id or "admin@yojnasetu.gov.in"
        now = datetime.utcnow()
        act = action.strip().upper()

        if act == "REJECT":
            update.status = "REJECTED"
            update.reviewed_at = now
            update.reviewed_by = admin_id
            update.rejection_reason = reason or "Rejected by administrative reviewer"
            target_db.commit()
            target_db.refresh(update)
            return update

        elif act == "APPROVE":
            prop_type = getattr(update, "proposal_type", "MODIFICATION")

            # Handle NEW_SCHEME promotion
            if prop_type == "NEW_SCHEME":
                candidate = None
                source = target_db.query(SchemeSource).filter(SchemeSource.source_id == update.source_id).first()
                if source:
                    candidate = target_db.query(CandidateScheme).filter(
                        CandidateScheme.official_source_url == source.source_url
                    ).first()

                if not candidate:
                    candidate = target_db.query(CandidateScheme).filter(
                        CandidateScheme.candidate_status.in_(["STAGED", "DISCOVERED"])
                    ).order_by(CandidateScheme.created_at.desc()).first()

                if candidate:
                    promoted = CandidatePromotionService.promote_candidate(
                        db=target_db,
                        candidate_id=candidate.candidate_id,
                        reviewer_id=admin_id,
                        notes=reason or f"Approved via pending update {update.update_id}"
                    )
                    update.scheme_id = promoted.scheme_id
                    update.status = "APPROVED"
                    update.reviewed_at = now
                    update.reviewed_by = admin_id
                    target_db.commit()
                    target_db.refresh(update)
                    return update
                else:
                    raise ValueError(f"No staged candidate found to promote for pending new scheme update '{update.update_id}'.")

            scheme = target_db.query(Scheme).filter(Scheme.scheme_id == update.scheme_id).first()
            if not scheme:
                raise ValueError(f"Target canonical scheme '{update.scheme_id}' does not exist in database.")

            extracted = json.loads(update.extracted_data) if update.extracted_data else {}
            changes = json.loads(update.detected_changes) if update.detected_changes else []

            # 1. Apply field updates and write changelog entries
            if prop_type == "DEACTIVATION":
                old_status = scheme.scheme_status or "ACTIVE"
                scheme.scheme_status = "INACTIVE"
                scheme.is_active = False
                target_db.add(SchemeChangelog(
                    scheme_id=scheme.scheme_id,
                    action="SCHEME_DEACTIVATED",
                    field="scheme_status",
                    old_value=old_status,
                    new_value="INACTIVE",
                    reason=reason or f"Approved scheme deactivation from source {update.source_id}",
                    admin_identifier=admin_id,
                    source_url=extracted.get("official_source_url") or scheme.official_source_url,
                    source_document=scheme.source_document or "Official Government Portal",
                    verification_status="VERIFIED",
                    created_at=now
                ))
            else:
                applied_changes = []
                for chg in changes:
                    field = chg["field"]
                    new_v = chg["new_value"]
                    old_v = chg["old_value"]

                    if hasattr(scheme, field):
                        setattr(scheme, field, new_v)
                        applied_changes.append(field)

                        target_db.add(SchemeChangelog(
                            scheme_id=scheme.scheme_id,
                            action="DYNAMIC_INGESTION_UPDATE",
                            field=field,
                            old_value=str(old_v) if old_v is not None else None,
                            new_value=str(new_v) if new_v is not None else None,
                            reason=reason or f"Approved dynamic ingestion update from source {update.source_id}",
                            admin_identifier=admin_id,
                            source_url=extracted.get("official_source_url") or scheme.official_source_url,
                            source_document=scheme.source_document or "Official Government Portal",
                            verification_status="VERIFIED",
                            created_at=now
                        ))

            # 2. Increment scheme version
            try:
                curr_ver = float(scheme.scheme_version or "1.0")
                new_ver = f"{curr_ver + 0.1:.1f}"
            except ValueError:
                new_ver = "1.1"

            scheme.previous_version = scheme.scheme_version or "1.0"
            scheme.scheme_version = new_ver
            scheme.last_verified_date = now.strftime("%Y-%m-%d")
            scheme.updated_at = now

            # 3. Update Pending Update state
            update.status = "APPROVED"
            update.reviewed_at = now
            update.reviewed_by = admin_id

            # 4. Trigger Eligibility Rules & RAG Knowledge synchronization
            IngestionSyncService.sync_after_approval(target_db, scheme, extracted)

            target_db.commit()
            target_db.refresh(update)
            target_db.refresh(scheme)
            return update

        else:
            raise ValueError(f"Invalid review action '{action}'. Must be APPROVE or REJECT.")

    @classmethod
    def list_pending_updates(
        cls,
        db: Session,
        status_filter: Optional[str] = None,
        scheme_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        query = db.query(PendingSchemeUpdate)

        if status_filter and status_filter.strip():
            query = query.filter(PendingSchemeUpdate.status == status_filter.strip().upper())
        if scheme_id and scheme_id.strip():
            query = query.filter(PendingSchemeUpdate.scheme_id == scheme_id.strip())

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(PendingSchemeUpdate.created_at.desc()).offset(offset).limit(page_size).all()

        formatted_items = []
        for u in items:
            try:
                extracted = json.loads(u.extracted_data) if u.extracted_data else {}
            except Exception:
                extracted = {}

            try:
                changes = json.loads(u.detected_changes) if u.detected_changes else []
            except Exception:
                changes = []

            try:
                val_errs = json.loads(u.validation_errors) if u.validation_errors else []
            except Exception:
                val_errs = []

            formatted_items.append({
                "update_id": u.update_id,
                "scheme_id": u.scheme_id,
                "source_id": u.source_id,
                "snapshot_id": u.snapshot_id,
                "proposal_type": getattr(u, "proposal_type", "MODIFICATION"),
                "change_classification": getattr(u, "change_classification", "MODIFIED"),
                "old_version": u.old_version,
                "extracted_data": extracted,
                "detected_changes": changes,
                "validation_status": u.validation_status,
                "validation_errors": val_errs,
                "status": u.status,
                "created_at": u.created_at,
                "reviewed_at": u.reviewed_at,
                "reviewed_by": u.reviewed_by,
                "rejection_reason": u.rejection_reason
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": formatted_items
        }

    @classmethod
    def get_pending_update_detail(cls, db: Session, update_id: str) -> Dict[str, Any]:
        update = db.query(PendingSchemeUpdate).filter(PendingSchemeUpdate.update_id == update_id).first()
        if not update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pending update with ID '{update_id}' not found."
            )

        extracted = json.loads(update.extracted_data) if update.extracted_data else {}
        changes = json.loads(update.detected_changes) if update.detected_changes else []
        val_errs = json.loads(update.validation_errors) if update.validation_errors else []

        return {
            "update_id": update.update_id,
            "scheme_id": update.scheme_id,
            "source_id": update.source_id,
            "snapshot_id": update.snapshot_id,
            "proposal_type": getattr(update, "proposal_type", "MODIFICATION"),
            "change_classification": getattr(update, "change_classification", "MODIFIED"),
            "old_version": update.old_version,
            "extracted_data": extracted,
            "detected_changes": changes,
            "validation_status": update.validation_status,
            "validation_errors": val_errs,
            "status": update.status,
            "created_at": update.created_at,
            "reviewed_at": update.reviewed_at,
            "reviewed_by": update.reviewed_by,
            "rejection_reason": update.rejection_reason
        }

    @classmethod
    def review_update(
        cls,
        db: Session,
        update_id: str,
        action: str,
        current_user: Union[User, str],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes administrative review decision (APPROVE or REJECT) on a pending update.
        """
        admin_id = getattr(current_user, "email", None) or getattr(current_user, "user_id", None) or str(current_user)
        instance = cls(db)
        try:
            update = instance.process_review(
                update_id=update_id,
                action=action,
                reviewer_id=admin_id,
                reason=reason
            )
            return {
                "update_id": update.update_id,
                "scheme_id": update.scheme_id,
                "status": update.status,
                "message": f"Pending update {update_id} review successfully completed (Status: {update.status})."
            }
        except ValueError as e:
            msg = str(e)
            if "not found" in msg:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
