import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference

logger = logging.getLogger("yojnasetu.notifications.providers")


class BaseNotificationProvider(ABC):
    @abstractmethod
    def send(self, db: Session, notification: Notification) -> bool:
        """Sends notification via the provider channel."""
        pass


class InAppNotificationProvider(BaseNotificationProvider):
    """
    Active provider: Persists notification to database for in-app delivery.
    """
    def send(self, db: Session, notification: Notification) -> bool:
        db.add(notification)
        logger.info(f"[IN_APP_DELIVERY] Saved notification {notification.notification_id} for user {notification.recipient_user_id}")
        return True


class EmailNotificationAdapter(BaseNotificationProvider):
    """
    Provider-ready adapter interface for external Email services (SendGrid/AWS SES).
    """
    def send(self, db: Session, notification: Notification) -> bool:
        logger.info(f"[EMAIL_ADAPTER_STUB] Simulating email delivery of '{notification.title}' to user {notification.recipient_user_id}")
        return True


class SMSNotificationAdapter(BaseNotificationProvider):
    """
    Provider-ready adapter interface for external SMS services (Twilio/CDAC DLT).
    """
    def send(self, db: Session, notification: Notification) -> bool:
        logger.info(f"[SMS_ADAPTER_STUB] Simulating SMS delivery of '{notification.title}' to user {notification.recipient_user_id}")
        return True


class WhatsAppNotificationAdapter(BaseNotificationProvider):
    """
    Provider-ready adapter interface for WhatsApp Business API.
    """
    def send(self, db: Session, notification: Notification) -> bool:
        logger.info(f"[WHATSAPP_ADAPTER_STUB] Simulating WhatsApp delivery of '{notification.title}' to user {notification.recipient_user_id}")
        return True


class PushNotificationAdapter(BaseNotificationProvider):
    """
    Provider-ready adapter interface for Mobile Push (Firebase FCM/WebPush).
    """
    def send(self, db: Session, notification: Notification) -> bool:
        logger.info(f"[PUSH_ADAPTER_STUB] Simulating Push delivery of '{notification.title}' to user {notification.recipient_user_id}")
        return True
