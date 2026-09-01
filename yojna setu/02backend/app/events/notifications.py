import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

logger = logging.getLogger("yojnasetu.notifications")


class NotificationEventType(str, Enum):
    APPLICATION_CREATED = "APPLICATION_CREATED"
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    APPLICATION_ASSIGNED = "APPLICATION_ASSIGNED"
    APPLICATION_UNDER_REVIEW = "APPLICATION_UNDER_REVIEW"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED"
    CORRECTION_REQUIRED = "CORRECTION_REQUIRED"
    APPLICATION_RESUBMITTED = "APPLICATION_RESUBMITTED"
    APPLICATION_APPROVED = "APPLICATION_APPROVED"
    APPLICATION_REJECTED = "APPLICATION_REJECTED"
    APPLICATION_WITHDRAWN = "APPLICATION_WITHDRAWN"
    APPLICATION_COMPLETED = "APPLICATION_COMPLETED"
    SYSTEM_INFO = "SYSTEM_INFO"
    SYSTEM_WARNING = "SYSTEM_WARNING"


class NotificationPublisher:
    _listeners: List[Any] = []

    @classmethod
    def publish(
        cls,
        db: Optional[Session],
        event_type: NotificationEventType,
        application_id: str,
        recipient_user_id: Optional[str] = None,
        recipient_role: Optional[str] = None,
        scheme_name: str = "",
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Publishes notification event and creates in-app database record if recipient_user_id is provided.
        """
        event_data = {
            "event_type": event_type.value,
            "application_id": application_id,
            "recipient_user_id": recipient_user_id,
            "recipient_role": recipient_role,
            "payload": payload or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.info(f"Notification Event Emitted: {event_data}")

        if db and recipient_user_id:
            try:
                from app.notifications.service import NotificationService
                NotificationService.create_notification(
                    db=db,
                    recipient_user_id=recipient_user_id,
                    notification_type=event_type.value,
                    application_id=application_id,
                    scheme_name=scheme_name,
                    extra_context=payload or {}
                )
            except Exception as e:
                logger.error(f"Failed to create notification record: {e}")

        return event_data
