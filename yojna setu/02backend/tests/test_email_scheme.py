import pytest
from unittest.mock import patch, MagicMock
import smtplib
from fastapi.testclient import TestClient

from app.main import app
from app.models.scheme import Scheme
from app.services.email_service import EmailService
from app.core.config import settings

client = TestClient(app)


@pytest.fixture
def test_client():
    return TestClient(app)


def test_email_scheme_api_valid_email(test_client):
    """Test POST /api/v1/schemes/{scheme_id}/email with a valid recipient email."""
    with patch("app.services.email_service.EmailService.send_scheme_email") as mock_send:
        mock_send.return_value = {
            "sent": True,
            "message": "Scheme details sent to your email (citizen.test@example.com).",
            "recipient_email": "citizen.test@example.com"
        }
        response = test_client.post(
            "/api/v1/schemes/SIH26092-001/email",
            json={"recipient_email": "citizen.test@example.com", "language_code": "en"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sent"] is True
        assert "recipient_email" in data
        assert data["recipient_email"] == "citizen.test@example.com"
        assert "sent to your email" in data["message"].lower()
        mock_send.assert_called_once()


def test_email_scheme_api_invalid_email_format(test_client):
    """Test POST /api/v1/schemes/{scheme_id}/email rejects malformed email with HTTP 422."""
    response = test_client.post(
        "/api/v1/schemes/SIH26092-001/email",
        json={"recipient_email": "not-an-email", "language_code": "en"}
    )
    assert response.status_code == 422


def test_email_scheme_api_nonexistent_scheme_404(test_client):
    """Test POST /api/v1/schemes/{scheme_id}/email returns 404 for invalid scheme ID."""
    response = test_client.post(
        "/api/v1/schemes/NONEXISTENT-999/email",
        json={"recipient_email": "citizen.test@example.com", "language_code": "en"}
    )
    assert response.status_code == 404


def test_email_service_smtp_mock_delivery():
    """Verify EmailService connects via STARTTLS, authenticates, and sends multi-part email."""
    mock_scheme = MagicMock()
    mock_scheme.scheme_id = "TEST-SCHEME-001"
    mock_scheme.scheme_name = "Test Welfare Scheme"
    mock_scheme.ministry = "Ministry of Social Justice"
    mock_scheme.purpose = "Promote financial inclusion"
    mock_scheme.short_description = "Promote financial inclusion"
    mock_scheme.financial_category = "LOAN_CREDIT"
    mock_scheme.max_loan_amount = 500000
    mock_scheme.subsidy_percentage = 25
    mock_scheme.interest_rate = 6.5
    mock_scheme.sector = "MICRO_FINANCE"
    mock_scheme.target_groups = "SC/ST Entrepreneurs"
    mock_scheme.marginalized_group = "SC"
    mock_scheme.application_url = "https://example.gov.in/apply"
    mock_scheme.official_portal = "https://example.gov.in"
    mock_scheme.application_route = "DIRECT_PORTAL"
    mock_scheme.partner_count = 0
    mock_scheme.documents = []

    with patch("app.core.config.settings.EMAIL_PROVIDER", "smtp"), \
         patch("app.core.config.settings.SMTP_HOST", "smtp.gmail.com"), \
         patch("app.core.config.settings.SMTP_PORT", 587), \
         patch("app.core.config.settings.SMTP_USERNAME", "sender@gmail.com"), \
         patch("app.core.config.settings.SMTP_PASSWORD", "secret_app_password"), \
         patch("app.core.config.settings.SMTP_FROM", "sender@gmail.com"), \
         patch("smtplib.SMTP") as mock_smtp_cls:

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = EmailService.send_scheme_email(
            recipient_email="beneficiary@gmail.com",
            scheme=mock_scheme,
            language_code="hi"
        )

        assert result["sent"] is True
        assert "beneficiary@gmail.com" in result["recipient_email"]

        # Verify SMTP interaction
        mock_smtp_cls.assert_called_with("smtp.gmail.com", 587, timeout=15)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_with("sender@gmail.com", "secret_app_password")
        mock_server.sendmail.assert_called_once()
        args, _ = mock_server.sendmail.call_args
        assert args[0] == "sender@gmail.com"
        assert args[1] == ["beneficiary@gmail.com"]
        assert "multipart/alternative" in args[2]


def test_email_service_smtp_auth_error_no_secret_leak():
    """Verify SMTPAuthenticationError returns safe error message without exposing credentials."""
    mock_scheme = MagicMock()
    mock_scheme.scheme_id = "TEST-001"
    mock_scheme.scheme_name = "Test Scheme"
    mock_scheme.ministry = "Govt"
    mock_scheme.purpose = "Desc"
    mock_scheme.short_description = "Desc"
    mock_scheme.financial_category = "LOAN"
    mock_scheme.max_loan_amount = 100000
    mock_scheme.subsidy_percentage = 0
    mock_scheme.interest_rate = 5
    mock_scheme.sector = "ALL"
    mock_scheme.target_groups = "ALL"
    mock_scheme.marginalized_group = None
    mock_scheme.application_url = None
    mock_scheme.official_portal = None
    mock_scheme.application_route = "DIRECT"
    mock_scheme.partner_count = 0
    mock_scheme.documents = []

    with patch("app.core.config.settings.EMAIL_PROVIDER", "smtp"), \
         patch("app.core.config.settings.SMTP_HOST", "smtp.gmail.com"), \
         patch("app.core.config.settings.SMTP_USERNAME", "sender@gmail.com"), \
         patch("app.core.config.settings.SMTP_PASSWORD", "super_secret_token_123"), \
         patch("smtplib.SMTP") as mock_smtp_cls:

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
        mock_smtp_cls.return_value.__enter__.return_value = mock_server

        result = EmailService.send_scheme_email(
            recipient_email="citizen@gmail.com",
            scheme=mock_scheme
        )

        assert result["sent"] is False
        assert "authentication error" in result["message"].lower()
        # Security assertion: password must NEVER be in the error message
        assert "super_secret_token_123" not in result["message"]
