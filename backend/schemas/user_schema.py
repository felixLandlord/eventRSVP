from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    ATTENDEE = "attendee"


class UserBase(BaseModel):
    email: EmailStr
    name: str
    avatar: Optional[str] = None
    role: UserRole = UserRole.ATTENDEE
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Email address validator"""
        # Ensures no spaces, valid domain, etc.
        email_regex: str = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid email format")

        # Block disposable domains
        disposable_domains: list = ["mailinator.com", "tempmail.com", "example.com"]
        domain: str = value.split("@")[1]
        if domain in disposable_domains:
            raise ValueError("Disposable email addresses are not allowed")

        return value.lower()


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str, info) -> str:
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
        if info.data:
            email: str = info.data.get("email", "").lower()
            first_name: str = info.data.get("first_name", "").lower()

            if email and email in value.lower():
                raise ValueError("Password cannot contain your email")
            if first_name and first_name in value.lower():
                raise ValueError("Password cannot contain your first name")

        return value


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    last_login: Optional[datetime] = None


class UserRead(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
