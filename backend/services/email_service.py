import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from jinja2 import Template
from pathlib import Path

from backend.core.config import settings
from backend.repository.user_repository import UserRepository
from backend.repository.event_repository import EventRepository


class EmailService:
    # TEMPLATE_DIR = Path("templates/emails")
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
            print(f"Failed to load template {template_name}: {e}")
            return None

    @staticmethod
    async def send_email(
        to_email: str, subject: str, body: str, is_html: bool = False
    ) -> bool:
        """Send email using SMTP"""
        try:
            if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
                print("Email credentials not configured")
                return False

            msg = MIMEMultipart("alternative")
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html" if is_html else "plain"))

            def send_smtp():
                server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                text = msg.as_string()
                server.sendmail(settings.SMTP_USERNAME, to_email, text)
                server.quit()

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_smtp)

            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )

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

        return await EmailService.send_email(
            user.email, subject, html_body, is_html=True
        )
