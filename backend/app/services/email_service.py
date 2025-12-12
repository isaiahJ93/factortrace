# app/services/email_service.py
"""
Email Service for Supplier Self-Serve Flow.

Handles:
- send_voucher_email: Sends voucher code after payment
- send_report_complete: Sends completed report notification with download links
- send_wizard_reminder: Reminds suppliers to complete their wizard session

Uses SendGrid for email delivery.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# EMAIL TEMPLATES
# =============================================================================

REPORT_COMPLETE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1e40af; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px 20px; background: #f9fafb; }}
        .button {{ display: inline-block; background: #1e40af; color: white;
                   padding: 12px 24px; text-decoration: none; border-radius: 4px;
                   margin: 10px 5px; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        .emissions-box {{ background: white; padding: 20px; border-radius: 8px;
                          margin: 20px 0; border: 1px solid #e5e7eb; }}
        .emissions-value {{ font-size: 32px; font-weight: bold; color: #1e40af; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your CSRD Compliance Report is Ready</h1>
        </div>
        <div class="content">
            <p>Dear {company_name},</p>

            <p>Great news! Your CSRD-compliant Scope 3 emissions report has been
            generated and is ready for download.</p>

            <div class="emissions-box">
                <h3>Your Total Emissions</h3>
                <div class="emissions-value">{total_emissions} tCO2e</div>
                <p>
                    Scope 1: {scope1_emissions} tCO2e<br>
                    Scope 2: {scope2_emissions} tCO2e<br>
                    Scope 3: {scope3_emissions} tCO2e
                </p>
            </div>

            <p>Download your reports:</p>

            <p style="text-align: center;">
                <a href="{pdf_url}" class="button">Download PDF Report</a>
                <a href="{xbrl_url}" class="button">Download XBRL/iXBRL</a>
            </p>

            <p>Your reports are also available anytime in your supplier portal:</p>
            <p style="text-align: center;">
                <a href="{portal_url}" class="button" style="background: #059669;">
                    View Supplier Portal
                </a>
            </p>

            <p><strong>What's next?</strong></p>
            <ul>
                <li>Share this report with your requesting buyer</li>
                <li>The PDF is print-ready for physical submissions</li>
                <li>The XBRL file is ready for ESRS digital reporting</li>
            </ul>

            <p>Questions? Reply to this email or contact
            <a href="mailto:support@factortrace.com">support@factortrace.com</a>.</p>
        </div>
        <div class="footer">
            <p>&copy; {year} FactorTrace. Regulatory Compliance Made Simple.</p>
            <p>This report was generated using emission factors from DEFRA 2024 and
            EXIOBASE 2020.</p>
        </div>
    </div>
</body>
</html>
"""

VOUCHER_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1e40af; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px 20px; background: #f9fafb; }}
        .voucher-box {{ background: #ecfdf5; border: 2px dashed #059669;
                        padding: 20px; text-align: center; margin: 20px 0;
                        border-radius: 8px; }}
        .voucher-code {{ font-size: 24px; font-weight: bold; color: #059669;
                         font-family: monospace; letter-spacing: 2px; }}
        .button {{ display: inline-block; background: #1e40af; color: white;
                   padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your FactorTrace Voucher</h1>
        </div>
        <div class="content">
            <p>Dear {company_name},</p>

            <p>Thank you for your purchase! Your CSRD compliance voucher is ready.</p>

            <div class="voucher-box">
                <p style="margin: 0 0 10px 0; color: #666;">Your Voucher Code:</p>
                <div class="voucher-code">{voucher_code}</div>
                <p style="margin: 10px 0 0 0; color: #666; font-size: 12px;">
                    Valid until: {valid_until}
                </p>
            </div>

            <p>You can start the compliance wizard right away:</p>

            <p style="text-align: center;">
                <a href="{wizard_url}" class="button">Start Compliance Wizard</a>
            </p>

            <p><strong>What you'll need:</strong></p>
            <ul>
                <li>Basic company information (name, country, industry)</li>
                <li>Activity data (electricity, fuel, travel, purchases)</li>
                <li>About 10 minutes of your time</li>
            </ul>

            <p>The wizard will guide you through each step. Your CSRD-compliant
            report will be generated automatically.</p>
        </div>
        <div class="footer">
            <p>&copy; {year} FactorTrace. Regulatory Compliance Made Simple.</p>
            <p>Questions? Contact <a href="mailto:support@factortrace.com">
            support@factortrace.com</a></p>
        </div>
    </div>
</body>
</html>
"""

WIZARD_REMINDER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f59e0b; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px 20px; background: #f9fafb; }}
        .button {{ display: inline-block; background: #1e40af; color: white;
                   padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
        .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Complete Your Compliance Report</h1>
        </div>
        <div class="content">
            <p>Dear {company_name},</p>

            <p>We noticed you started your CSRD compliance wizard but haven't
            completed it yet. You're currently on step: <strong>{current_step}</strong>.</p>

            <p>Your voucher is still valid until <strong>{valid_until}</strong>.</p>

            <p style="text-align: center;">
                <a href="{wizard_url}" class="button">Continue Where You Left Off</a>
            </p>

            <p>Need help? Our support team is ready to assist you at
            <a href="mailto:support@factortrace.com">support@factortrace.com</a>.</p>
        </div>
        <div class="footer">
            <p>&copy; {year} FactorTrace. Regulatory Compliance Made Simple.</p>
        </div>
    </div>
</body>
</html>
"""


# =============================================================================
# EMAIL SERVICE CLASS
# =============================================================================

class EmailService:
    """
    Email service for supplier communications.

    Uses SendGrid API for email delivery.
    Falls back to logging in development if SendGrid not configured.
    """

    def __init__(self):
        self.sendgrid_key = settings.sendgrid_api_key
        self.from_email = "reports@factortrace.com"
        self.from_name = "FactorTrace"

    async def send_report_complete(
        self,
        *,
        to_email: str,
        company_name: str,
        total_emissions: float,
        scope1_emissions: float,
        scope2_emissions: float,
        scope3_emissions: float,
        pdf_url: str,
        xbrl_url: Optional[str] = None,
        portal_url: Optional[str] = None,
    ) -> bool:
        """
        Send report completion email with download links.

        Args:
            to_email: Recipient email
            company_name: Company name
            total_emissions: Total tCO2e
            scope1_emissions: Scope 1 tCO2e
            scope2_emissions: Scope 2 tCO2e
            scope3_emissions: Scope 3 tCO2e
            pdf_url: URL to download PDF report
            xbrl_url: URL to download XBRL (optional)
            portal_url: URL to supplier portal (optional)

        Returns:
            True if email sent successfully
        """
        subject = f"Your CSRD Compliance Report is Ready - {company_name}"

        html_content = REPORT_COMPLETE_TEMPLATE.format(
            company_name=company_name,
            total_emissions=f"{total_emissions:,.2f}",
            scope1_emissions=f"{scope1_emissions:,.2f}",
            scope2_emissions=f"{scope2_emissions:,.2f}",
            scope3_emissions=f"{scope3_emissions:,.2f}",
            pdf_url=pdf_url,
            xbrl_url=xbrl_url or pdf_url,  # Fallback to PDF URL
            portal_url=portal_url or "https://app.factortrace.com/portal",
            year=datetime.utcnow().year,
        )

        return await self._send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )

    async def send_voucher_email(
        self,
        *,
        to_email: str,
        company_name: str,
        voucher_code: str,
        valid_until: datetime,
        wizard_url: Optional[str] = None,
    ) -> bool:
        """
        Send voucher email after payment.

        Args:
            to_email: Recipient email
            company_name: Company name
            voucher_code: The voucher code
            valid_until: Voucher expiration date
            wizard_url: URL to start wizard (optional)

        Returns:
            True if email sent successfully
        """
        subject = f"Your FactorTrace Compliance Voucher - {voucher_code}"

        html_content = VOUCHER_EMAIL_TEMPLATE.format(
            company_name=company_name,
            voucher_code=voucher_code,
            valid_until=valid_until.strftime("%B %d, %Y"),
            wizard_url=wizard_url or "https://app.factortrace.com/wizard",
            year=datetime.utcnow().year,
        )

        return await self._send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )

    async def send_wizard_reminder(
        self,
        *,
        to_email: str,
        company_name: str,
        current_step: str,
        valid_until: datetime,
        wizard_url: Optional[str] = None,
    ) -> bool:
        """
        Send reminder to complete wizard session.

        Args:
            to_email: Recipient email
            company_name: Company name
            current_step: Current wizard step
            valid_until: Voucher expiration date
            wizard_url: URL to continue wizard (optional)

        Returns:
            True if email sent successfully
        """
        subject = f"Complete Your CSRD Compliance Report - {company_name}"

        # Human-readable step names
        step_names = {
            "company_profile": "Company Profile",
            "activity_data": "Activity Data Entry",
            "review": "Review & Calculate",
            "generate_report": "Generate Report",
        }
        step_display = step_names.get(current_step, current_step)

        html_content = WIZARD_REMINDER_TEMPLATE.format(
            company_name=company_name,
            current_step=step_display,
            valid_until=valid_until.strftime("%B %d, %Y"),
            wizard_url=wizard_url or "https://app.factortrace.com/wizard",
            year=datetime.utcnow().year,
        )

        return await self._send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
        )

    async def _send_email(
        self,
        *,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """
        Send email via SendGrid.

        Falls back to logging in development if SendGrid not configured.
        """
        if not self.sendgrid_key:
            logger.warning(
                f"SendGrid not configured. Would send email to {to_email}: {subject}"
            )
            logger.debug(f"Email content:\n{html_content[:500]}...")
            return True  # Return True in dev mode

        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content

            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_key)

            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
            )

            response = sg.send(message)

            if response.status_code in (200, 201, 202):
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            else:
                logger.error(
                    f"SendGrid returned status {response.status_code}: {response.body}"
                )
                return False

        except ImportError:
            logger.warning("sendgrid package not installed, email not sent")
            return False
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get singleton email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


async def send_report_complete_email(
    to_email: str,
    company_name: str,
    emissions: Dict[str, float],
    pdf_url: str,
    xbrl_url: Optional[str] = None,
) -> bool:
    """
    Convenience function to send report completion email.

    Args:
        to_email: Recipient email
        company_name: Company name
        emissions: Dict with scope1_tco2e, scope2_tco2e, scope3_tco2e, total_tco2e
        pdf_url: URL to download PDF
        xbrl_url: URL to download XBRL (optional)

    Returns:
        True if sent successfully
    """
    service = get_email_service()
    return await service.send_report_complete(
        to_email=to_email,
        company_name=company_name,
        total_emissions=emissions.get("total_tco2e", 0),
        scope1_emissions=emissions.get("scope1_tco2e", 0),
        scope2_emissions=emissions.get("scope2_tco2e", 0),
        scope3_emissions=emissions.get("scope3_tco2e", 0),
        pdf_url=pdf_url,
        xbrl_url=xbrl_url,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "EmailService",
    "get_email_service",
    "send_report_complete_email",
]
