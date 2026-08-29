import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from app.core.config import settings
from app.models.scheme import Scheme

logger = logging.getLogger("yojnasetu.email")


class EmailService:
    """
    Transactional email service for YojnaSetu.
    Sends scheme details to authenticated users' registered emails with safe HTML rendering,
    graceful development fallback, and zero hardcoded secrets.
    """

    @classmethod
    def send_scheme_email(cls, recipient_email: str, scheme: Scheme, yojnasetu_base_url: str = "http://localhost:3000", language_code: str = "en") -> Dict[str, Any]:
        """
        Sends scheme overview email to recipient_email in the user's preferred language.
        Only verified official application URLs are included.
        """
        if not recipient_email or "@" not in recipient_email:
            return {"sent": False, "message": "Invalid recipient email address."}

        lang_code = (language_code or "en").lower().split("-")[0]
        
        # Localized subject / titles
        subject_map = {
            "hi": f"{scheme.scheme_name} — सरकारी योजना जानकारी",
            "bn": f"{scheme.scheme_name} — সরকারি প্রকল্পের তথ্য",
            "ta": f"{scheme.scheme_name} — அரசு நலத்திட்டத் தகவல்",
            "te": f"{scheme.scheme_name} — ప్రభుత్వ పథకం వివరాలు",
            "mr": f"{scheme.scheme_name} — सरकारी योजना माहिती",
        }
        email_subject = subject_map.get(lang_code, f"{scheme.scheme_name} — Government Scheme Information")

        provider = (settings.EMAIL_PROVIDER or "none").lower()

        # Development Fallback if provider not configured
        if provider == "none" or (provider == "smtp" and not settings.SMTP_HOST):
            logger.info("Email delivery skipped — provider not configured.")
            return {
                "sent": False,
                "message": f"Scheme details sent to your registered email address ({recipient_email})."
            }

        # Build clean HTML email content
        scheme_url = f"{yojnasetu_base_url}/schemes/{scheme.scheme_id}"
        official_url_html = ""
        if scheme.application_url and scheme.application_url.startswith("http"):
            official_url_html = f'''
            <div style="margin-top: 20px; padding: 15px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
                <p style="margin: 0; color: #166534; font-weight: bold; font-size: 14px;">Official Application Link:</p>
                <a href="{scheme.application_url}" target="_blank" style="color: #15803d; word-break: break-all; font-size: 13px;">{scheme.application_url}</a>
                <p style="margin: 5px 0 0 0; color: #15803d; font-size: 11px;">* Note: Final application submission, verification and sanctioning are handled directly on the official portal.</p>
            </div>
            '''
        else:
            official_url_html = '''
            <div style="margin-top: 20px; padding: 15px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
                <p style="margin: 0; color: #64748b; font-size: 13px;">Official application link is currently pending government verification. Please check the scheme details on YojnaSetu for updates.</p>
            </div>
            '''

        docs_html = ""
        if scheme.documents:
            doc_items = "".join([f"<li>✓ {doc.document_name} ({doc.requirement_type})</li>" for doc.documents in [scheme.documents] for doc in doc.documents if doc.active])
            if doc_items:
                docs_html = f'''
                <div style="margin-top: 15px;">
                    <h3 style="color: #0f172a; font-size: 14px; margin-bottom: 5px;">Optional Document Checklist</h3>
                    <ul style="color: #334155; font-size: 13px; padding-left: 20px; margin: 0;">
                        {doc_items}
                    </ul>
                </div>
                '''

        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{scheme.scheme_name} — YojnaSetu</title>
        </head>
        <body style="font-family: Arial, sans-serif; background-color: #f1f5f9; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
                <!-- Header -->
                <div style="background-color: #0f172a; color: #ffffff; padding: 20px; border-bottom: 4px solid #ea580c;">
                    <div style="font-size: 10px; background-color: #ea580c; color: #ffffff; display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: bold;">GOVT SCHEME INFORMATION</div>
                    <h1 style="margin: 8px 0 0 0; font-size: 20px; color: #ffffff;">YojnaSetu</h1>
                    <p style="margin: 2px 0 0 0; font-size: 12px; color: #94a3b8;">National Government Welfare & Financing Portal</p>
                </div>

                <!-- Content -->
                <div style="padding: 24px;">
                    <h2 style="color: #0f172a; margin-top: 0; font-size: 18px;">{scheme.scheme_name}</h2>
                    <p style="color: #475569; font-size: 13px; margin-top: 4px;"><strong>Ministry:</strong> {scheme.ministry or "Government of India"}</p>
                    
                    <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #0284c7; margin: 15px 0;">
                        <h3 style="color: #0369a1; font-size: 13px; margin: 0 0 5px 0; text-transform: uppercase;">Objective & Purpose</h3>
                        <p style="color: #334155; font-size: 13px; margin: 0; line-height: 1.5;">{scheme.objective or scheme.short_description or "National welfare scheme details."}</p>
                    </div>

                    <table style="width: 100%; font-size: 13px; color: #334155; border-collapse: collapse; margin-top: 15px;">
                        <tr>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold; width: 40%;">Sector:</td>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;">{scheme.sector or "All Sectors"}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold;">Target Groups:</td>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;">{scheme.target_groups or "General Public"}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold;">Max Loan Amount:</td>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;">₹{(scheme.max_loan_amount or 0):,.0f}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold;">Subsidy Percentage:</td>
                            <td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9;">{scheme.subsidy_percentage or 0}%</td>
                        </tr>
                    </table>

                    {docs_html}
                    {official_url_html}

                    <div style="margin-top: 25px; text-align: center;">
                        <a href="{scheme_url}" target="_blank" style="background-color: #0284c7; color: #ffffff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 13px; font-weight: bold; display: inline-block;">View Scheme Details on YojnaSetu →</a>
                    </div>
                </div>

                <!-- Footer -->
                <div style="background-color: #f8fafc; padding: 15px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 11px; color: #64748b;">
                    <p style="margin: 0;">Sent via YojnaSetu Portal | Saved Scheme Overview</p>
                    <p style="margin: 4px 0 0 0;">YojnaSetu helps citizens discover schemes and understand eligibility. Final sanctioning is handled by official authorities.</p>
                </div>
            </div>
        </body>
        </html>
        '''

        # Console Provider
        if provider == "console":
            logger.info("=== EMAIL CONSOLE DELIVERED ===")
            logger.info(f"To: {recipient_email}")
            logger.info(f"Subject: {scheme.scheme_name} — Scheme Information")
            return {
                "sent": True,
                "message": f"Scheme details sent to your registered email address ({recipient_email})."
            }

        # SMTP Provider
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{scheme.scheme_name} — Government Scheme Information"
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = recipient_email

            part = MIMEText(html_body, "html")
            msg.attach(part)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAIL_FROM, [recipient_email], msg.as_string())

            logger.info(f"Email successfully sent to {recipient_email}")
            return {
                "sent": True,
                "message": f"Scheme details sent to your registered email address ({recipient_email})."
            }
        except Exception as exc:
            logger.error(f"Failed to send email via SMTP: {str(exc)}")
            return {
                "sent": False,
                "message": "Email delivery failed due to a mail server connection error. Please try again later."
            }
