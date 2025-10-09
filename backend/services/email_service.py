import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import asyncio
from contextlib import asynccontextmanager
from backend.core.config import settings
from backend.core.logger import get_logger
from backend.core.errors import EmailServiceError

logger = get_logger("email_service")

class EmailService:
    """Async email service using aiosmtplib"""
    
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.max_retries = 3
        self.timeout = 30.0

    @asynccontextmanager
    async def _get_smtp_connection(self):
        """Create and manage async SMTP connection"""
        smtp = aiosmtplib.SMTP(
            hostname=self.host,
            port=self.port,
            timeout=self.timeout
        )
        try:
            if self.use_tls:
                await smtp.starttls()
            if self.username and self.password:
                await smtp.login(self.username, self.password)
            yield smtp
        finally:
            try:
                await smtp.quit()
            except Exception:
                pass

    async def _handle_email_errors(self, func, *args, **kwargs):
        """Handle email errors with exponential backoff retry"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except aiosmtplib.SMTPException as e:
                delay = (2 ** attempt) + asyncio.rand() * 0.5
                logger.warning(f"Email attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise EmailServiceError(f"Failed to send email after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(delay)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        is_html: bool = False
    ):
        """
        Send email asynchronously with retry logic
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            is_html: Whether the body contains HTML content
        
        Raises:
            EmailServiceError: If email sending fails after retries
        """
        message = MIMEMultipart()
        message["From"] = self.username
        message["To"] = to_email
        message["Subject"] = subject
        
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)

        content_type = "html" if is_html else "plain"
        message.attach(MIMEText(body, content_type))

        async with self._get_smtp_connection() as smtp:
            await self._handle_email_errors(
                smtp.send_message,
                message,
                self.username,
                [to_email] + (cc or []) + (bcc or [])
            )