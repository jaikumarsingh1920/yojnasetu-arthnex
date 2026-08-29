import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.notifications.templates import build_notification_content
from app.notifications.providers import (
    InAppNotificationProvider,
    EmailNotificationAdapter,
    SMSNotificationAdapter,
    WhatsAppNotificationAdapter,
    PushNotificationAdapter
)


class NotificationService:
    @classmethod
    def get_or_create_preferences(cls, db: Session, user_id: str) -> NotificationPreference:
        prefs = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not prefs:
            prefs = NotificationPreference(
                user_id=user_id,
                in_app_enabled=True,
                email_enabled=True,
                sms_enabled=True,
                whatsapp_enabled=False,
                push_enabled=False
            )
            db.add(prefs)
            db.flush()
        return prefs

    @classmethod
    def create_notification(
        cls,
        db: Session,
        recipient_user_id: str,
        notification_type: str,
        application_id: Optional[str] = None,
        scheme_name: str = "",
        extra_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Notification]:
        """
        Creates and dispatches a notification for recipient_user_id.
        Evaluates recipient preferences and delivers via enabled channels.
        """
        if not recipient_user_id:
            return None

        prefs = cls.get_or_create_preferences(db, recipient_user_id)

        # Build content and deep links
        title, message, priority, metadata_json = build_notification_content(
            notification_type=notification_type,
            application_id=application_id or "",
            scheme_name=scheme_name,
            extra_context=extra_context
        )

        notification = Notification(
            recipient_user_id=recipient_user_id,
            application_id=application_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            is_read=False,
            created_at=datetime.utcnow(),
            metadata_json=metadata_json,
            channel="IN_APP",
            delivery_status="DELIVERED"
        )

        # In-App Delivery
        if prefs.in_app_enabled:
            InAppNotificationProvider().send(db, notification)

        # External Adapters (Stubs logged cleanly)
        if prefs.email_enabled:
            EmailNotificationAdapter().send(db, notification)
        if prefs.sms_enabled:
            SMSNotificationAdapter().send(db, notification)
        if prefs.whatsapp_enabled:
            WhatsAppNotificationAdapter().send(db, notification)
        if prefs.push_enabled:
            PushNotificationAdapter().send(db, notification)

        return notification

    @classmethod
    def get_user_notifications(
        cls,
        db: Session,
        recipient_user_id: str,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Notification], int]:
        """
        Retrieves paginated notifications for recipient_user_id.
        Sorted by newest first.
        """
        query = db.query(Notification).filter(Notification.recipient_user_id == recipient_user_id)

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        if notification_type:
            query = query.filter(Notification.notification_type == notification_type)

        total = query.count()
        items = query.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    @classmethod
    def get_unread_count(cls, db: Session, recipient_user_id: str) -> int:
        return db.query(Notification).filter(
            Notification.recipient_user_id == recipient_user_id,
            Notification.is_read == False
        ).count()

    @classmethod
    def mark_read(cls, db: Session, notification_id: str, recipient_user_id: str) -> Optional[Notification]:
        notif = db.query(Notification).filter(
            Notification.notification_id == notification_id,
            Notification.recipient_user_id == recipient_user_id
        ).first()

        if notif:
            if not notif.is_read:
                notif.is_read = True
                notif.read_at = datetime.utcnow()
                db.flush()
        return notif

    @classmethod
    def mark_all_read(cls, db: Session, recipient_user_id: str) -> int:
        now = datetime.utcnow()
        updated_count = db.query(Notification).filter(
            Notification.recipient_user_id == recipient_user_id,
            Notification.is_read == False
        ).update(
            {Notification.is_read: True, Notification.read_at: now},
            synchronize_session=False
        )
        db.flush()
        return updated_count
