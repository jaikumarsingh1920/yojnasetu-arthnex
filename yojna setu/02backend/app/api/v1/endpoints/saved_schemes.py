import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.scheme import Scheme
from app.models.saved_scheme import SavedScheme
from app.schemas.saved_scheme import (
    SavedSchemeResponse,
    SavedSchemeStatusResponse,
    SavedSchemeListResponse,
    EmailSchemeResponse,
)
from app.schemas.scheme import EmailSchemeRequest
from app.services.email_service import EmailService

logger = logging.getLogger("yojnasetu.api.saved_schemes")
router = APIRouter()


@router.post("/{scheme_id}", response_model=SavedSchemeResponse, status_code=status.HTTP_201_CREATED)
def save_scheme(
    scheme_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Saves a government scheme to the current user's account.
    Idempotent: If already saved, returns the existing saved scheme record.
    """
    scheme = db.query(Scheme).filter(Scheme.scheme_id == scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' does not exist."
        )

    existing = db.query(SavedScheme).filter(
        SavedScheme.user_id == current_user.user_id,
        SavedScheme.scheme_id == scheme_id
    ).first()

    if existing:
        return existing

    saved_obj = SavedScheme(
        user_id=current_user.user_id,
        scheme_id=scheme_id
    )
    db.add(saved_obj)
    db.commit()
    db.refresh(saved_obj)
    logger.info(f"User '{current_user.user_id}' saved scheme '{scheme_id}'")
    return saved_obj


@router.delete("/{scheme_id}", status_code=status.HTTP_200_OK)
def remove_saved_scheme(
    scheme_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Removes a scheme from the current user's saved schemes list.
    Idempotent: If not found, returns success.
    """
    saved_obj = db.query(SavedScheme).filter(
        SavedScheme.user_id == current_user.user_id,
        SavedScheme.scheme_id == scheme_id
    ).first()

    if saved_obj:
        db.delete(saved_obj)
        db.commit()
        logger.info(f"User '{current_user.user_id}' removed scheme '{scheme_id}' from saved list")

    return {"message": f"Scheme '{scheme_id}' removed from saved schemes.", "scheme_id": scheme_id}


@router.get("", response_model=SavedSchemeListResponse)
def list_saved_schemes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieves all saved schemes for the authenticated user, ordered by saved date.
    Strictly isolated to the current user's account.
    """
    items = db.query(SavedScheme).filter(
        SavedScheme.user_id == current_user.user_id
    ).order_by(SavedScheme.created_at.desc()).all()

    return SavedSchemeListResponse(
        items=items,
        total=len(items)
    )


@router.get("/{scheme_id}", response_model=SavedSchemeStatusResponse)
def check_saved_status(
    scheme_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Checks whether the current user has saved a specific scheme.
    """
    saved_obj = db.query(SavedScheme).filter(
        SavedScheme.user_id == current_user.user_id,
        SavedScheme.scheme_id == scheme_id
    ).first()

    return SavedSchemeStatusResponse(
        scheme_id=scheme_id,
        is_saved=saved_obj is not None
    )


@router.post("/{scheme_id}/email", response_model=EmailSchemeResponse)
def email_scheme(
    scheme_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    req: Optional[EmailSchemeRequest] = Body(None),
) -> Any:
    """
    Emails scheme details to the recipient email address (defaults to current_user.email).
    """
    scheme = db.query(Scheme).filter(Scheme.scheme_id == scheme_id).first()
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' does not exist."
        )

    recipient_email = (str(req.recipient_email).strip() if req and req.recipient_email else (current_user.email or current_user.phone))
    if not recipient_email or "@" not in recipient_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You do not have a valid registered email address associated with your account. Please update your email profile."
        )

    lang = (req.language_code if req and req.language_code else getattr(current_user, "preferred_language", "en")) or "en"
    result = EmailService.send_scheme_email(
        recipient_email=recipient_email,
        scheme=scheme,
        language_code=lang
    )
    return EmailSchemeResponse(
        sent=result["sent"],
        message=result["message"],
        recipient_email=recipient_email
    )
