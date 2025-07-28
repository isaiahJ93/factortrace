# app/tasks.py
from celery import shared_task, Task
from celery.exceptions import MaxRetriesExceededError
import logging
from typing import Dict, Any
from datetime import datetime
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.core.config import settings
from app.core.celery_app import celery_app
import boto3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailTask(Task):
    """Base task with email client initialization"""
    _email_client = None
    
    @property
    def email_client(self):
        if self._email_client is None:
            if settings.EMAIL_PROVIDER == "sendgrid":
                self._email_client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            elif settings.EMAIL_PROVIDER == "ses":
                self._email_client = boto3.client(
                    'ses',
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )
        return self._email_client

@shared_task(bind=True, base=EmailTask, max_retries=3, default_retry_delay=60)
def send_email_task(self, email_data: Dict[str, Any]):
    """Send email with automatic retry on failure"""
    try:
        logger.info(f"Sending email to {email_data['to']}")
        
        if settings.EMAIL_PROVIDER == "sendgrid":
            message = Mail(
                from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
                to_emails=To(email_data['to']),
                subject=email_data['subject'],
                html_content=self._render_template(email_data['template'], email_data['context'])
            )
            
            response = self.email_client.send(message)
            logger.info(f"Email sent successfully. Status: {response.status_code}")
            
        elif settings.EMAIL_PROVIDER == "ses":
            response = self.email_client.send_email(
                Source=f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                Destination={'ToAddresses': [email_data['to']]},
                Message={
                    'Subject': {'Data': email_data['subject']},
                    'Body': {
                        'Html': {
                            'Data': self._render_template(email_data['template'], email_data['context'])
                        }
                    }
                }
            )
            logger.info(f"Email sent via SES. MessageId: {response['MessageId']}")
            
        # Log success to monitoring
        record_email_sent.delay(email_data['to'], email_data['template'])
        
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        # Exponential backoff retry
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render email template with context"""
        templates = {
            "voucher": """
                <html>
                <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                        <h1 style="color: #333; text-align: center;">Your FactorTrace Compliance Voucher</h1>
                        
                        <p>Dear {company_name},</p>
                        
                        <p>Thank you for your purchase! Your emissions compliance voucher is ready.</p>
                        
                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h2 style="color: #0066cc; text-align: center; margin: 0;">Voucher Code</h2>
                            <p style="font-size: 24px; font-weight: bold; text-align: center; margin: 10px 0; color: #333;">
                                {voucher_code}
                            </p>
                            <p style="text-align: center; color: #666; margin: 0;">Valid until: {valid_until}</p>
                        </div>
                        
                        <h3>How to use your voucher:</h3>
                        <ol>
                            <li>Go to <a href="https://app.factortrace.com/redeem">app.factortrace.com/redeem</a></li>
                            <li>Enter your voucher code</li>
                            <li>Complete your company information</li>
                            <li>Start tracking your emissions</li>
                        </ol>
                        
                        <p>Your voucher includes:</p>
                        <ul>
                            <li>Full emissions tracking for Scope 1, 2, and 3</li>
                            <li>ESRS E1 compliant reporting</li>
                            <li>XBRL export for regulatory submission</li>
                            <li>12 months of access</li>
                        </ul>
                        
                        <p>Need help? Contact us at <a href="mailto:{support_email}">{support_email}</a></p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        <p style="color: #666; font-size: 12px; text-align: center;">
                            FactorTrace - Simplifying Emissions Compliance<br>
                            This voucher is non-transferable and subject to our terms of service.
                        </p>
                    </div>
                </body>
                </html>
            """,
            "report_ready": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h1>Your Emissions Report is Ready</h1>
                    <p>Hello {company_name},</p>
                    <p>Your {report_type} emissions report has been generated and is ready for download.</p>
                    <p><a href="{download_link}" style="background-color: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Report</a></p>
                    <p>This link will expire in 7 days.</p>
                </body>
                </html>
            """,
            "reminder": """
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h1>Compliance Deadline Reminder</h1>
                    <p>Hello {company_name},</p>
                    <p>This is a reminder that your emissions report is due in {days_remaining} days.</p>
                    <p>Current completion: {completion_percentage}%</p>
                    <p><a href="https://app.factortrace.com/dashboard">Complete Your Report</a></p>
                </body>
                </html>
            """
        }
        
        template = templates.get(template_name, "")
        return template.format(**context)

@shared_task(bind=True, max_retries=5)
def generate_emissions_report(self, voucher_id: int, report_format: str = "xbrl"):
    """Generate emissions report - can take several minutes"""
    try:
        logger.info(f"Starting report generation for voucher {voucher_id}")
        
        # Import here to avoid circular imports
        from app.services.xbrl_exporter import XBRLExporter
        from app.db.session import SessionLocal
        from app.models.voucher import Voucher
        from app.models.emission import Emission
        
        db = SessionLocal()
        try:
            voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
            if not voucher:
                raise ValueError(f"Voucher {voucher_id} not found")
                
            # Get all emissions for this company
            emissions = db.query(Emission).filter(
                Emission.company_id == voucher.company_id
            ).all()
            
            # Generate report
            exporter = XBRLExporter()
            report_path = exporter.generate_report(emissions, voucher.company_name)
            
            # Upload to S3 or storage
            download_url = upload_report_to_storage(report_path)
            
            # Send completion email
            send_email_task.delay({
                "to": voucher.company_email,
                "subject": "Your Emissions Report is Ready",
                "template": "report_ready",
                "context": {
                    "company_name": voucher.company_name,
                    "report_type": "ESRS E1 Compliance",
                    "download_link": download_url
                }
            })
            
            logger.info(f"Report generated successfully for voucher {voucher_id}")
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Report generation failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes

@shared_task
def record_email_sent(email: str, template: str):
    """Record email metrics for monitoring"""
    # In production, send to monitoring system
    logger.info(f"Email metric: {template} sent to {email}")

@shared_task
def cleanup_expired_vouchers():
    """Daily task to cleanup expired unused vouchers"""
    from app.db.session import SessionLocal
    from app.models.voucher import Voucher
    
    db = SessionLocal()
    try:
        expired_count = db.query(Voucher).filter(
            Voucher.valid_until < datetime.utcnow(),
            Voucher.is_used == False
        ).update({"is_expired": True})
        
        db.commit()
        logger.info(f"Marked {expired_count} vouchers as expired")
        
    finally:
        db.close()

@shared_task
def send_compliance_reminders():
    """Send reminders for upcoming compliance deadlines"""
    from app.db.session import SessionLocal
    from app.models.voucher import Voucher
    from datetime import timedelta
    
    db = SessionLocal()
    try:
        # Find vouchers expiring in 30 days
        warning_date = datetime.utcnow() + timedelta(days=30)
        
        vouchers = db.query(Voucher).filter(
            Voucher.valid_until <= warning_date,
            Voucher.valid_until > datetime.utcnow(),
            Voucher.is_used == True,
            Voucher.reminder_sent == False
        ).all()
        
        for voucher in vouchers:
            days_remaining = (voucher.valid_until - datetime.utcnow()).days
            
            send_email_task.delay({
                "to": voucher.company_email,
                "subject": f"Compliance Deadline in {days_remaining} days",
                "template": "reminder",
                "context": {
                    "company_name": voucher.company_name,
                    "days_remaining": days_remaining,
                    "completion_percentage": calculate_completion_percentage(voucher.id)
                }
            })
            
            voucher.reminder_sent = True
            
        db.commit()
        logger.info(f"Sent {len(vouchers)} compliance reminders")
        
    finally:
        db.close()

def calculate_completion_percentage(voucher_id: int) -> int:
    """Calculate report completion percentage"""
    # Implementation depends on your business logic
    return 75  # Placeholder

def upload_report_to_storage(report_path: str) -> str:
    """Upload report to S3 or similar storage"""
    # Implementation for S3 upload
    # Return presigned URL
    return f"https://storage.factortrace.com/reports/{report_path}"

# Celery Beat Schedule (add to celery config)
celery_app.conf.beat_schedule = {
    'cleanup-expired-vouchers': {
        'task': 'app.tasks.cleanup_expired_vouchers',
        'schedule': 60.0 * 60 * 24,  # Daily
    },
    'send-compliance-reminders': {
        'task': 'app.tasks.send_compliance_reminders',
        'schedule': 60.0 * 60 * 24,  # Daily
    },
}