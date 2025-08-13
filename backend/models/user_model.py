import re
import secrets
import string
from typing import Optional
from datetime import datetime
from sqlalchemy import (
    String,
    Boolean,
    Enum,
    DateTime,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from backend.models.base_model import Base, TimestampMixin
from backend.schemas.user_schema import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"
    # id: Mapped[uuid.UUID] = mapped_column(
    #     UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    # )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.ATTENDEE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    email_otp: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email_otp_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_reset_otp: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    password_reset_otp_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a random numeric OTP"""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    @validates("email")
    def validate_email(self, key, value: str) -> str:
        """Email address validator"""
        email_regex: str = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid email format")

        # Block disposable domains
        disposable_domains: list = [
            "mailinator.com",
            "tempmail.com",
            "example.com",
        ]
        domain: str = value.split("@")[1]
        if domain.lower() in disposable_domains:
            raise ValueError("Disposable email addresses are not allowed")

        return value.lower()

    @validates("password")
    def validate_password(self, key, value: str) -> str:
        """Password validator"""
        # Complexity checks
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit")

        # No common weak patterns
        weak_passwords: list = ["password", "12345678", "qwerty"]
        if any(weak in value.lower() for weak in weak_passwords):
            raise ValueError("Password is too common or weak")

        # Prevent password containing email or name
        if hasattr(self, "email") and self.email:
            if self.email.lower() in value.lower():
                raise ValueError("Password cannot contain your email")
        if hasattr(self, "name") and self.name:
            if self.name.lower() in value.lower():
                raise ValueError("Password cannot contain your name")

        return value
