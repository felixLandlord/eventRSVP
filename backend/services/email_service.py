import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from jinja2 import Template
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed

from backend.core.config import settings
from backend.repository.user_repository import UserRepository
from backend.repository.event_repository import EventRepository
from backend.core.exceptions import EmailError


class EmailService:
    TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"

    @staticmethod
    def _load_template(template_name: str) -> Optional[Template]:
        """Load email template from file"""
        try:
            template_path = EmailService.TEMPLATE_DIR / template_name
            with open(template_path, "r", encoding="utf-8") as file:
                template_content = file.read()
            return Template(template_content)
        except Exception as e:
            raise EmailError(message=f"Failed to load template {template_name}", code="TEMPLATE_ERROR", original_error=e)

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def send_email(
        to_email: str, subject: str, body: str, is_html: bool = False
    ) -> bool:
        """Send email using async SMTP"""
        try:
            if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
                raise EmailError("Email credentials not configured", code="CREDENTIALS_MISSING")

            msg = MIMEMultipart("alternative")
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html" if is_html else "plain"))

            smtp = aiosmtplib.SMTP(
                hostname=settings.SMTP_SERVER,
                port=settings.SMTP_PORT,
                use_tls=True,
            )

            await smtp.connect()
            await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            await smtp.send_message(msg)
            await smtp.quit()

            return True
        except Exception as e:
            raise EmailError(message="Failed to send email", code="EMAIL_ERROR", original_error=e)

    # Other email methods remain the same but now raise exceptions instead of printing errors.