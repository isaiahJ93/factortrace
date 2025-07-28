# app/services/email_service.py (CREATE NEW FILE)
import logging
from typing import Optional
from datetime import datetime
import asyncio
from app.core.config import settings
from app.tasks import send_email_task
import aioredis
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.redis = None
        
    async def _get_redis(self):
        if not self.redis:
            self.redis = await aioredis.from_url(settings.REDIS_URL)
        return self.redis
        
    async def send_voucher_email(
        self,
        to_email: str,
        company_name: str,
        voucher_code: str,
        valid_until: datetime
    ):
        """Queue voucher email for sending"""
        email_data = {
            "to": to_email,
            "subject": f"Your FactorTrace Emissions Compliance Voucher - {voucher_code}",
            "template": "voucher",
            "context": {
                "company_name": company_name,
                "voucher_code": voucher_code,
                "valid_until": valid_until.strftime("%B %d, %Y"),
                "support_email": "support@factortrace.com"
            }
        }
        
        # Add to queue with retry logic
        send_email_task.apply_async(
            args=[email_data],
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.2,
            }
        )
        
        logger.info(f"Queued voucher email for {to_email}")