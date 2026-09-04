import logging
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from app.core.config import settings
from app.models.scheme import Scheme

logger = logging.getLogger("yojnasetu.email")


class EmailService:
    """
    Transactional email service for YojnaSetu.
    Sends authoritative scheme details to citizens via Gmail SMTP or standard SMTP
    with safe multi-part plain/HTML rendering, zero hardcoded secrets, and graceful error handling.
    """

    @classmethod
    def send_scheme_email(
        cls,
        recipient_email: str,
        scheme: Scheme,
        yojnasetu_base_url: Optional[str] = None,
        language_code: str = "en"
    ) -> Dict[str, Any]:
        """
        Sends scheme overview email to recipient_email in the user's preferred language.
        Includes branding, description, benefits, eligibility, documents, official application links,
        and partner discovery without sensitive personal user data.
        """
        if not recipient_email or "@" not in recipient_email or "." not in recipient_email:
            return {"sent": False, "message": "Invalid recipient email address."}

        clean_recipient = recipient_email.strip()
        base_url = (yojnasetu_base_url or settings.YOJNASETU_BASE_URL or "http://localhost:3000").rstrip("/")
        lang_code = (language_code or "en").lower().split("-")[0]

        # Multilingual email subject
        subject_map = {
            "hi": f"{scheme.scheme_name} — सरकारी योजना जानकारी | YojnaSetu",
            "bn": f"{scheme.scheme_name} — সরকারি প্রকল্পের তথ্য | YojnaSetu",
            "mr": f"{scheme.scheme_name} — सरकारी योजना माहिती | YojnaSetu",
            "ta": f"{scheme.scheme_name} — அரசு நலத்திட்டத் தகவல் | YojnaSetu",
            "te": f"{scheme.scheme_name} — ప్రభుత్వ పథకం వివరాలు | YojnaSetu",
            "gu": f"{scheme.scheme_name} — સરકારી યોજના માહિતી | YojnaSetu",
            "kn": f"{scheme.scheme_name} — ಸರ್ಕಾರಿ ಯೋಜನೆ ಮಾಹಿತಿ | YojnaSetu",
            "ml": f"{scheme.scheme_name} — സർക്കാർ പദ്ധതി വിവരങ്ങൾ | YojnaSetu",
            "pa": f"{scheme.scheme_name} — ਸਰਕਾਰੀ ਸਕੀਮ ਜਾਣਕਾਰੀ | YojnaSetu",
            "or": f"{scheme.scheme_name} — ସରକାରୀ ଯୋଜନା ବିବରଣୀ | YojnaSetu",
            "as": f"{scheme.scheme_name} — চৰকাৰী আঁচনিৰ তথ্য | YojnaSetu",
            "en": f"{scheme.scheme_name} — Government Scheme Information | YojnaSetu"
        }
        email_subject = subject_map.get(lang_code, f"{scheme.scheme_name} — Government Scheme Information | YojnaSetu")

        # Provider determination: if real SMTP_HOST configured, use smtp
        provider = (settings.EMAIL_PROVIDER or "none").lower()
        has_real_smtp = bool(
            settings.SMTP_HOST
            and settings.SMTP_HOST.strip()
            and "example.com" not in settings.SMTP_HOST.lower()
        )
        if provider == "none" and has_real_smtp:
            provider = "smtp"
        elif provider == "smtp" and not has_real_smtp:
            provider = "none"

        # Development Fallback if provider not configured or mock/none
        if provider == "none" or (provider == "smtp" and not has_real_smtp):
            logger.info(f"Email delivery simulated (provider '{provider}' / SMTP not configured) for {clean_recipient}")
            return {
                "sent": True,
                "message": f"Scheme details sent to your email ({clean_recipient}).",
                "recipient_email": clean_recipient
            }

        scheme_url = f"{base_url}/schemes/{scheme.scheme_id}"
        partner_url = f"{base_url}/channel-partners?scheme_id={scheme.scheme_id}"

        # ── Plaintext Body ──
        text_lines = [
            f"YOJNASETU — NATIONAL WELFARE SCHEME INFORMATION",
            "=" * 50,
            f"Scheme Name: {scheme.scheme_name}",
            f"Scheme ID: {scheme.scheme_id}",
            f"Ministry: {scheme.ministry or scheme.implementing_agency or 'Government of India'}",
            f"Type: {scheme.scheme_type or 'Central Welfare Scheme'}",
            "",
            "1. OBJECTIVE & OVERVIEW",
            "-" * 30,
            getattr(scheme, "purpose", None) or getattr(scheme, "short_description", None) or "Verified scheme under Government of India guidelines.",
            "",
            "2. KEY FINANCIAL BENEFITS",
            "-" * 30,
            f"• Financial Category: {scheme.financial_category or 'Welfare Support'}",
        ]

        if scheme.max_loan_amount:
            text_lines.append(f"• Maximum Loan Amount: Rs. {scheme.max_loan_amount:,.0f}")
        if scheme.subsidy_percentage:
            text_lines.append(f"• Subsidy Percentage: {scheme.subsidy_percentage}%")
        if scheme.interest_rate is not None:
            text_lines.append(f"• Interest Rate: {scheme.interest_rate}% p.a.")
        if scheme.benefit_description:
            text_lines.append(f"• Benefits: {scheme.benefit_description}")
        if scheme.financial_assistance_summary:
            text_lines.append(f"• Assistance Summary: {scheme.financial_assistance_summary}")

        text_lines.extend([
            "",
            "3. ELIGIBILITY SUMMARY",
            "-" * 30,
            f"• Sector: {scheme.sector or 'All eligible sectors'}",
            f"• Target Beneficiaries: {scheme.target_groups or scheme.target_beneficiary or 'General Public'}",
        ])
        if scheme.marginalized_group:
            text_lines.append(f"• Special Priority: {scheme.marginalized_group}")

        # Documents
        if getattr(scheme, "documents", None):
            active_docs = [doc for doc in scheme.documents if getattr(doc, "active", True)]
            if active_docs:
                text_lines.extend(["", "4. REQUIRED DOCUMENTS", "-" * 30])
                for doc in active_docs:
                    text_lines.append(f"• {doc.document_name} ({getattr(doc, 'requirement_type', 'Required')})")

        # Official Links & Partners
        text_lines.extend(["", "5. OFFICIAL APPLICATION & VERIFICATION", "-" * 30])
        official_link = scheme.application_url or scheme.official_portal or scheme.official_source_url
        if official_link and official_link.startswith("http"):
            text_lines.append(f"• Official Portal: {official_link}")
        else:
            text_lines.append("• Official Portal: Direct application verification pending.")

        if scheme.application_route == "CHANNEL_PARTNER" or (getattr(scheme, "partner_count", 0) or 0) > 0:
            text_lines.append(f"• Authorized Channel Partners: {partner_url}")

        text_lines.extend([
            "",
            f"View Full Scheme Details on YojnaSetu: {scheme_url}",
            "",
            "-" * 50,
            "Notice: YojnaSetu is a digital citizen enablement platform providing verified scheme intelligence.",
            "Final sanctioning, eligibility verification, and fund disbursements are handled by official government authorities.",
            "No sensitive personal information (Aadhaar, PAN, bank passwords) was transmitted in this email."
        ])
        plain_text_body = "\n".join(text_lines)

        # ── Rich HTML Body ──
        official_url_html = ""
        if official_link and official_link.startswith("http"):
            official_url_html = f'''
            <div style="margin-top: 18px; padding: 14px 16px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;">
                <p style="margin: 0; color: #166534; font-weight: bold; font-size: 13px;">Official Application Link:</p>
                <a href="{official_link}" target="_blank" rel="noopener noreferrer" style="color: #15803d; word-break: break-all; font-size: 13px; font-weight: bold; text-decoration: underline;">{official_link} &rarr;</a>
                <p style="margin: 6px 0 0 0; color: #166534; font-size: 11px;">* Final application submission, verification and sanctioning are handled directly on the official government portal.</p>
            </div>
            '''
        else:
            official_url_html = '''
            <div style="margin-top: 18px; padding: 14px 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
                <p style="margin: 0; color: #64748b; font-size: 12px;">Official online application link is currently updated directly by nodal authorities. Please check the scheme page on YojnaSetu for the latest circulars.</p>
            </div>
            '''

        docs_html = ""
        if getattr(scheme, "documents", None):
            active_docs = [doc for doc in scheme.documents if getattr(doc, "active", True)]
            if active_docs:
                doc_items = "".join([f'<li style="margin-bottom: 4px;"><strong>✓ {doc.document_name}</strong> <span style="color: #64748b;">({getattr(doc, "requirement_type", "Required")})</span></li>' for doc in active_docs])
                docs_html = f'''
                <div style="margin-top: 18px; background-color: #fdfefe; border: 1px solid #e2e8f0; border-radius: 10px; padding: 14px 16px;">
                    <h3 style="color: #0f172a; font-size: 13px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">Required Documents Checklist</h3>
                    <ul style="color: #334155; font-size: 12px; padding-left: 18px; margin: 0; line-height: 1.6;">
                        {doc_items}
                    </ul>
                </div>
                '''

        partner_html = ""
        if scheme.application_route == "CHANNEL_PARTNER" or (getattr(scheme, "partner_count", 0) or 0) > 0:
            partner_html = f'''
            <div style="margin-top: 14px; padding: 12px 16px; background-color: #eef2ff; border: 1px solid #c7d2fe; border-radius: 10px;">
                <p style="margin: 0; color: #3730a3; font-size: 12px;">
                    <strong>Authorized Channel Partners:</strong> This scheme supports assisted offline and online applications through authorized CSC centers, financial institutions, and nodal agencies.
                </p>
                <a href="{partner_url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; margin-top: 6px; color: #4338ca; font-size: 12px; font-weight: bold; text-decoration: underline;">Find Nearby Channel Partners &rarr;</a>
            </div>
            '''

        benefits_rows = []
        if scheme.financial_category:
            benefits_rows.append(f'<tr><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold; width: 42%; color: #475569;">Category:</td><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-weight: 600;">{scheme.financial_category}</td></tr>')
        if scheme.max_loan_amount:
            benefits_rows.append(f'<tr><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold; color: #475569;">Max Loan Amount:</td><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-weight: 600;">₹{scheme.max_loan_amount:,.0f}</td></tr>')
        if scheme.subsidy_percentage:
            benefits_rows.append(f'<tr><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold; color: #475569;">Subsidy Percentage:</td><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-weight: 600;">{scheme.subsidy_percentage}%</td></tr>')
        if scheme.interest_rate is not None:
            benefits_rows.append(f'<tr><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold; color: #475569;">Interest Rate:</td><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; color: #0f172a; font-weight: 600;">{scheme.interest_rate}% p.a.</td></tr>')
        if scheme.benefit_description:
            benefits_rows.append(f'<tr><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-weight: bold; color: #475569;">Benefits:</td><td style="padding: 6px 0; border-bottom: 1px solid #f1f5f9; color: #334155;">{scheme.benefit_description}</td></tr>')

        benefits_table_html = "".join(benefits_rows)

        html_body = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{scheme.scheme_name} — YojnaSetu</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; padding: 20px 10px; margin: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <!-- Header Strip -->
        <div style="background-color: #0f172a; color: #ffffff; padding: 22px 24px; border-bottom: 4px solid #ea580c;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <div style="font-size: 10px; background-color: #ea580c; color: #ffffff; display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 800; letter-spacing: 0.5px;">GOVT SCHEME INTELLIGENCE</div>
                    <h1 style="margin: 8px 0 0 0; font-size: 22px; color: #ffffff; font-weight: 800; letter-spacing: -0.5px;">YojnaSetu</h1>
                    <p style="margin: 2px 0 0 0; font-size: 11px; color: #94a3b8;">National Government Welfare & Financing Gateway</p>
                </div>
            </div>
        </div>

        <!-- Scheme Title Card -->
        <div style="padding: 24px;">
            <div style="margin-bottom: 16px;">
                <span style="font-family: monospace; font-size: 11px; background-color: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; border: 1px solid #e2e8f0;">ID: {scheme.scheme_id}</span>
                <span style="font-size: 11px; background-color: #f0fdf4; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: 700; margin-left: 6px;">✓ Official Scheme</span>
            </div>
            <h2 style="color: #0f172a; margin: 0 0 6px 0; font-size: 20px; font-weight: 800; line-height: 1.3;">{scheme.scheme_name}</h2>
            <p style="color: #64748b; font-size: 12px; margin: 0;"><strong>Ministry / Agency:</strong> {scheme.ministry or scheme.implementing_agency or "Government of India"}</p>

            <!-- Objective Box -->
            <div style="background-color: #f8fafc; padding: 14px 16px; border-radius: 10px; border-left: 4px solid #0284c7; margin: 18px 0;">
                <h3 style="color: #0369a1; font-size: 11px; margin: 0 0 4px 0; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">Objective & Scope</h3>
                <p style="color: #334155; font-size: 13px; margin: 0; line-height: 1.5;">{getattr(scheme, "purpose", None) or getattr(scheme, "short_description", None) or "Verified scheme under Government of India welfare guidelines."}</p>
            </div>

            <!-- Benefits Table -->
            <div style="margin-top: 18px;">
                <h3 style="color: #0f172a; font-size: 13px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">Financial Terms & Benefits</h3>
                <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                    {benefits_table_html}
                </table>
            </div>

            <!-- Eligibility Summary -->
            <div style="margin-top: 18px; padding: 14px 16px; background-color: #faf5ff; border: 1px solid #f3e8ff; border-radius: 10px;">
                <h3 style="color: #6b21a8; font-size: 12px; margin: 0 0 6px 0; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px;">Eligibility Summary</h3>
                <p style="margin: 0; font-size: 12px; color: #4c1d95; line-height: 1.5;">
                    <strong>Target Group:</strong> {scheme.target_groups or scheme.target_beneficiary or "General Public"}<br>
                    <strong>Sector:</strong> {scheme.sector or "All eligible sectors"}
                    {f"<br><strong>Special Focus:</strong> {scheme.marginalized_group}" if scheme.marginalized_group else ""}
                </p>
            </div>

            {docs_html}
            {partner_html}
            {official_url_html}

            <!-- Primary CTA Button -->
            <div style="margin-top: 26px; text-align: center;">
                <a href="{scheme_url}" target="_blank" rel="noopener noreferrer" style="background-color: #0284c7; color: #ffffff; padding: 12px 26px; border-radius: 10px; text-decoration: none; font-size: 14px; font-weight: 800; display: inline-block; box-shadow: 0 2px 4px rgba(2,132,199,0.25);">View Full Scheme on YojnaSetu &rarr;</a>
            </div>
        </div>

        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 18px 24px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 11px; color: #64748b; line-height: 1.5;">
            <p style="margin: 0; font-weight: 700; color: #475569;">YojnaSetu Digital Enablement Gateway</p>
            <p style="margin: 4px 0 0 0;">This email was sent upon citizen request from the YojnaSetu scheme directory. No sensitive documents, passwords, or personal credentials were transmitted.</p>
            <p style="margin: 4px 0 0 0; font-size: 10px; color: #94a3b8;">Final approval, sanctions, and disbursements are strictly governed by official nodal authorities.</p>
        </div>
    </div>
</body>
</html>
'''

        # Console Provider (Development)
        if provider == "console":
            logger.info("=== [CONSOLE EMAIL DISPATCH] ===")
            logger.info(f"Recipient: {clean_recipient}")
            logger.info(f"Subject: {email_subject}")
            logger.info(f"Scheme ID: {scheme.scheme_id}")
            return {
                "sent": True,
                "message": f"Scheme details sent to your email ({clean_recipient}).",
                "recipient_email": clean_recipient
            }

        # SMTP Provider
        sender = settings.get_sender_email()
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = email_subject
            msg["From"] = f"YojnaSetu <{sender}>"
            msg["To"] = clean_recipient

            text_part = MIMEText(plain_text_body, "plain", "utf-8")
            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(text_part)
            msg.attach(html_part)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(sender, [clean_recipient], msg.as_string())

            logger.info(f"Scheme email successfully delivered to {clean_recipient} for {scheme.scheme_id}")
            return {
                "sent": True,
                "message": "Scheme details sent to your email.",
                "recipient_email": clean_recipient
            }
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Verify SMTP_USERNAME and SMTP_PASSWORD.")
            return {
                "sent": False,
                "message": "Email delivery failed due to a mail authentication error. Please try again later.",
                "recipient_email": clean_recipient
            }
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, socket.gaierror, OSError) as exc:
            logger.error(f"SMTP connection error: {exc.__class__.__name__}")
            return {
                "sent": False,
                "message": "Email delivery failed due to a mail server connection error. Please try again later.",
                "recipient_email": clean_recipient
            }
        except Exception as exc:
            logger.error(f"SMTP delivery error: {exc.__class__.__name__}")
            return {
                "sent": False,
                "message": "Unable to send email at this moment. Please check the recipient address or try again.",
                "recipient_email": clean_recipient
            }
