from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.notifications.service import NotificationService
from app.schemas.notification import (
    NotificationResponse,
    PaginatedNotificationListResponse,
    UnreadCountResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedNotificationListResponse,
    summary="Get current user notifications"
)
def get_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read/unread status"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of notifications for the current authenticated user.
    Sorted newest first.
    """
    items, total = NotificationService.get_user_notifications(
        db=db,
        recipient_user_id=current_user.user_id,
        is_read=is_read,
        notification_type=notification_type,
        page=page,
        page_size=page_size
    )
    unread_count = NotificationService.get_unread_count(db, current_user.user_id)

    return PaginatedNotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get count of unread notifications"
)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = NotificationService.get_unread_count(db, current_user.user_id)
    return UnreadCountResponse(unread_count=count)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a specific notification as read"
)
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notif = NotificationService.mark_read(db, notification_id, current_user.user_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' was not found."
        )
    db.commit()
    db.refresh(notif)
    return notif


@router.post(
    "/read-all",
    summary="Mark all current user notifications as read"
)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_count = NotificationService.mark_all_read(db, current_user.user_id)
    db.commit()
    return {"message": "All notifications marked as read.", "count": updated_count}


@router.get(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Get user notification preferences"
)
def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = NotificationService.get_or_create_preferences(db, current_user.user_id)
    db.commit()
    return prefs


@router.put(
    "/preferences",
    response_model=NotificationPreferenceResponse,
    summary="Update user notification preferences"
)
def update_notification_preferences(
    req: NotificationPreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prefs = NotificationService.get_or_create_preferences(db, current_user.user_id)

    if req.in_app_enabled is not None:
        prefs.in_app_enabled = req.in_app_enabled
    if req.email_enabled is not None:
        prefs.email_enabled = req.email_enabled
    if req.sms_enabled is not None:
        prefs.sms_enabled = req.sms_enabled
    if req.whatsapp_enabled is not None:
        prefs.whatsapp_enabled = req.whatsapp_enabled
    if req.push_enabled is not None:
        prefs.push_enabled = req.push_enabled

    db.commit()
    db.refresh(prefs)
    return prefs


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Get single notification detail"
)
def get_notification_detail(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from app.models.notification import Notification
    notif = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.recipient_user_id == current_user.user_id
    ).first()

    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification '{notification_id}' was not found."
        )
    return notif
