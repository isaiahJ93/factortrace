import os
from typing import List, Dict
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(settings.SENDGRID_API_KEY) if settings.SENDGRID_API_KEY else None
        self.from_email = Email(settings.FROM_EMAIL, settings.FROM_NAME)
    
    def send_voucher_email(
        self, 
        to_email: str, 
        company_name: str, 
        vouchers: List[Dict[str, str]], 
        total_amount: int,
        package_name: str
    ):
        """Send voucher codes to customer after purchase"""
        
        if not self.sg:
            logger.warning("SendGrid not configured - skipping email")
            return False
        
        # Create voucher list HTML
        voucher_list_html = ""
        for i, voucher in enumerate(vouchers, 1):
            voucher_list_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">#{i}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; font-family: monospace; font-weight: bold;">{voucher['code']}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; color: #22c55e;">Active</td>
            </tr>
            """
        
        # Email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Your FactorTrace Compliance Vouchers</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #000; color: #fff; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">✅ Payment Confirmed</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Your compliance vouchers are ready</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                <p>Hi {company_name},</p>
                
                <p>Thank you for your purchase! Your <strong>{len(vouchers)} compliance voucher(s)</strong> are now active and ready to use.</p>
                
                <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0;">
                    <strong>Quick Start:</strong> Visit <a href="https://app.factortrace.com/redeem">app.factortrace.com/redeem</a> and enter any voucher code below to begin your first compliance report.
                </div>
                
                <h2 style="margin-top: 30px;">Your Voucher Codes</h2>
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <thead>
                        <tr style="background-color: #f3f4f6;">
                            <th style="padding: 12px; text-align: left;">#</th>
                            <th style="padding: 12px; text-align: left;">Voucher Code</th>
                            <th style="padding: 12px; text-align: left;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {voucher_list_html}
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; padding: 20px; background-color: #f0fdf4; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: #16a34a;">What's Next?</h3>
                    <ol style="margin: 10px 0; padding-left: 20px;">
                        <li>Share voucher codes with your portfolio companies</li>
                        <li>Each company uses a code to create their account</li>
                        <li>Complete ESRS E1 compliance in 47 minutes</li>
                        <li>Download audit-ready reports instantly</li>
                    </ol>
                </div>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280;">
                    <p><strong>Order Details:</strong></p>
                    <p>Package: {package_name}<br>
                    Amount: €{total_amount:,.2f}<br>
                    Vouchers: {len(vouchers)}<br>
                    Valid: 12 months from purchase</p>
                    
                    <p style="margin-top: 20px;">Need help? Reply to this email or contact support@factortrace.com</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Payment Confirmed - Your FactorTrace Compliance Vouchers
        
        Hi {company_name},
        
        Thank you for your purchase! Your {len(vouchers)} compliance voucher(s) are now active.
        
        YOUR VOUCHER CODES:
        {chr(10).join([f"{i}. {v['code']}" for i, v in enumerate(vouchers, 1)])}
        
        Quick Start: Visit app.factortrace.com/redeem and enter any voucher code above.
        
        Order Details:
        - Package: {package_name}
        - Amount: €{total_amount:,.2f}
        - Vouchers: {len(vouchers)}
        - Valid: 12 months from purchase
        
        Need help? Contact support@factortrace.com
        """
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=f"Your {len(vouchers)} FactorTrace Compliance Vouchers",
            plain_text_content=Content("text/plain", text_content),
            html_content=Content("text/html", html_content)
        )
        
        try:
            response = self.sg.send(message)
            logger.info(f"Email sent to {to_email}, status: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_test_email(self, to_email: str):
        """Send a test email to verify configuration"""
        
        if not self.sg:
            return False, "SendGrid not configured"
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject="FactorTrace Email Test",
            html_content="<p>This is a test email from FactorTrace. If you received this, email integration is working correctly!</p>"
        )
        
        try:
            response = self.sg.send(message)
            return True, f"Test email sent! Status: {response.status_code}"
        except Exception as e:
            return False, f"Failed to send test email: {str(e)}"

# Singleton instance
email_service = EmailService()
