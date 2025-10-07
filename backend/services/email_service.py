import aiosmtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from jinja2 import Template
from pathlib import Path

from backend.core.config import settings
from backend.repository.user_repository import UserRepository
from backend.repository.event_repository import EventRepository


class EmailService:
    TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    @staticmethod
    def _load_template(template_name: str) -> Optional[Template]:
        """Load email template from file"""
        try:
            template_path = EmailService.TEMPLATE_DIR / template_name
            with open(template_path, "r", encoding="utf-8") as file:
                template_content = file.read()
            return Template(template_content)
        except Exception as e:
            print(f"Failed to load template {template_name}: {e}")
            return None

    @staticmethod
    def _create_message(to_email: str, subject: str, body: str, is_html: bool) -> MIMEMultipart:
        """Create email message with proper headers and content"""
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html" if is_html else "plain"))
        return msg

    @staticmethod
    async def send_email(
        to_email: str, subject: str, body: str, is_html: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Send email using async SMTP"""
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            return False, "Email credentials not configured"

        msg = EmailService._create_message(to_email, subject, body, is_html)
        
        for attempt in range(EmailService.MAX_RETRIES):
            try:
                smtp = aiosmtplib.SMTP(hostname=settings.SMTP_SERVER, 
                                     port=settings.SMTP_PORT, 
                                     use_tls=True)
                
                await smtp.connect()
                await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                await smtp.send_message(msg)
                await smtp.quit()
                
                return True, None
                
            except aiosmtplib.SMTPException as e:
                error_msg = f"SMTP error on attempt {attempt + 1}: {str(e)}"
                if attempt < EmailService.MAX_RETRIES - 1:
                    await asyncio.sleep(EmailService.RETRY_DELAY * (2 ** attempt))
                    continue
                return False, error_msg
                
            except Exception as e:
                return False, f"Unexpected error: {str(e)}"

    @staticmethod
    async def send_account_created(user_id: int) -> bool:
        """Send account created confirmation email"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return False

        template = EmailService._load_template("account_created.html")
        if not template:
            return False

        subject = "Welcome to EventHub!"
        html_body = template.render(first_name=user.name, email=user.email)

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_account_deleted(user_id: int, recovery_link: str) -> bool:
        """Send account deleted notification email"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return False

        template = EmailService._load_template("account_deleted.html")
        if not template:
            return False

        subject = "Account Deleted - EventHub"
        html_body = template.render(first_name=user.name, recovery_link=recovery_link)

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_account_updated(user_id: int, email_changed: bool = False) -> bool:
        """Send account updated notification email"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return False

        template = EmailService._load_template("account_updated.html")
        if not template:
            return False

        email_changed_block = ""
        if email_changed:
            email_changed_block = """
            <div class="note">
                <p><strong>Important:</strong> Your email address has been changed. 
                If this wasn't you, please contact our support team immediately.</p>
            </div>
            """

        subject = "Account Updated - EventHub"
        html_body = template.render(
            first_name=user.name, email_changed_block=email_changed_block
        )

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_account_verified(user_id: int) -> bool:
        """Send account verified confirmation email"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return False

        template = EmailService._load_template("account_verified.html")
        if not template:
            return False

        subject = "Account Verified Successfully - EventHub"
        html_body = template.render(first_name=user.name)

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_email_otp(user_id: int, otp: str) -> bool:
        """Send email verification OTP"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return False

        template = EmailService._load_template("email_otp.html")
        if not template:
            return False

        subject = "Email Verification OTP - EventHub"
        html_body = template.render(first_name=user.name, otp=otp)

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_forgot_password(user_id: int, otp: str) -> bool:
        """Send forgot password OTP"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return False

        template = EmailService._load_template("forgot_password.html")
        if not template:
            return False

        subject = "Password Reset Request - EventHub"
        html_body = template.render(first_name=user.name, otp=otp)

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_password_reset(user_id: int) -> bool:
        """Send password reset confirmation"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            return False

        template = EmailService._load_template("password_reset.html")
        if not template:
            return False

        subject = "Password Reset Successful - EventHub"
        html_body = template.render(first_name=user.name)

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_rsvp_confirmation(user_id: int, event_id: int) -> bool:
        """Send RSVP confirmation email"""
        user = await UserRepository.get_by_id(user_id)
        event = await EventRepository.get_by_id(event_id)

        if not user or not event:
            return False

        template = EmailService._load_template("rsvp_confirmation.html")
        if not template:
            return False

        subject = f"RSVP Confirmation - {event.title}"
        html_body = template.render(
            first_name=user.name,
            event_title=event.title,
            event_date=event.start_date.strftime("%B %d, %Y at %I:%M %p"),
            event_location=event.location,
            event_description=event.description,
        )

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success

    @staticmethod
    async def send_event_reminder(user_id: int, event_id: int) -> bool:
        """Send event reminder email"""
        user = await UserRepository.get_by_id(user_id)
        event = await EventRepository.get_by_id(event_id)

        if not user or not event:
            return False

        template = EmailService._load_template("event_reminder.html")
        if not template:
            return False

        subject = f"Event Reminder - {event.title} is tomorrow!"
        html_body = template.render(
            first_name=user.name,
            event_title=event.title,
            event_date=event.start_date.strftime("%B %d, %Y at %I:%M %p"),
            event_location=event.location,
        )

        success, _ = await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
        return success