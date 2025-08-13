# services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Literal
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError

from backend.repository.user_repository import UserRepository
from backend.repository.refresh_token_repository import RefreshTokenRepository
from backend.graphql_api.types import (
    RegisterInput,
    LoginInput,
    AuthType,
    UserType,
    VerifyEmailInput,
    ResendOTPInput,
    ForgotPasswordInput,
    ResetPasswordInput,
    ChangePasswordInput,
)
from backend.core.config import settings

from backend.schemas.user_schema import UserCreate, UserUpdate
from backend.services.email_service import EmailService
from backend.models.user_model import User


class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return AuthService.pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return AuthService.pwd_context.hash(password)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _encode(payload: dict, expires_delta: timedelta) -> str:
        to_encode = payload.copy()
        to_encode["exp"] = AuthService._now() + expires_delta
        return jwt.encode(
            to_encode, settings.SESSION_SECRET_KEY, algorithm=settings.ALGORITHM
        )

    @staticmethod
    def decode_token(token: str, verify_exp: bool = True) -> dict:
        return jwt.decode(
            token,
            settings.SESSION_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": verify_exp},
        )

    @staticmethod
    def _validate_token_payload(
        payload: dict, expected_type: Literal["access", "refresh"]
    ) -> str:
        if payload.get("type") != expected_type:
            raise ValueError(f"Not a {expected_type} token")
        email = payload.get("sub")
        if not isinstance(email, str):
            raise ValueError("Invalid subject in token")
        return email

    @staticmethod
    def create_access_token(email: str) -> str:
        return AuthService._encode(
            {"sub": email, "type": "access"},
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    @staticmethod
    def create_refresh_token(email: str) -> tuple[str, datetime]:
        expires_at = AuthService._now() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        token = AuthService._encode(
            {"sub": email, "type": "refresh"},
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return token, expires_at

    @staticmethod
    async def register(user_data: RegisterInput) -> str:
        existing_user = await UserRepository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered!")

        hashed_password = AuthService.get_password_hash(user_data.password)

        user = UserCreate(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
            is_active=False,
        )
        created_user = await UserRepository.create(user)
        await AuthService._send_email_verification_otp(created_user.id, user_data.email)
        return "Registration successful! Please check your email for verification code."

    @staticmethod
    async def login(login_data: LoginInput) -> AuthType:
        user = await UserRepository.get_by_email(login_data.email)
        if not user or not AuthService.verify_password(
            login_data.password, user.password
        ):
            raise ValueError("Invalid email or password!")

        if user.is_deleted:
            raise ValueError(
                "Account has been deleted. Please contact support for recovery."
            )

        if not user.is_active:
            raise ValueError("Account is inactive. Please contact support.")

        await RefreshTokenRepository.invalidate_all_for_user(user.id)

        user.last_login = datetime.now(timezone.utc)
        await UserRepository.update(user.id, UserUpdate(last_login=user.last_login))

        access_token = AuthService.create_access_token(user.email)
        refresh_token, expires_at = AuthService.create_refresh_token(user.email)

        await RefreshTokenRepository.create(user.id, refresh_token, expires_at)

        return AuthType(
            user=UserType(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                avatar=user.avatar,
                created_at=user.created_at,
            ),
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @staticmethod
    async def refresh_tokens(old_refresh_token: str) -> AuthType:
        try:
            payload = AuthService.decode_token(old_refresh_token, verify_exp=True)
            email = AuthService._validate_token_payload(payload, "refresh")
        except ExpiredSignatureError:
            raise ValueError("Refresh token expired")
        except JWTError:
            raise ValueError("Invalid refresh token")

        stored_token = await RefreshTokenRepository.get(old_refresh_token)
        if not stored_token:
            raise ValueError("Refresh token not found or already used")

        await RefreshTokenRepository.delete(old_refresh_token)

        user = await UserRepository.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        new_access_token = AuthService.create_access_token(user.email)
        new_refresh_token, expires_at = AuthService.create_refresh_token(user.email)

        await RefreshTokenRepository.create(user.id, new_refresh_token, expires_at)

        return AuthType(
            user=UserType(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                avatar=user.avatar,
                created_at=user.created_at,
            ),
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )

    @staticmethod
    async def get_current_user(token: str) -> UserType:
        email = AuthService._validate_token_payload(
            AuthService.decode_token(token, verify_exp=True), "access"
        )
        user = await UserRepository.get_by_email(email)
        if not user:
            raise ValueError("User not found or inactive")
        return UserType(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            avatar=user.avatar,
            created_at=user.created_at,
        )

    @staticmethod
    async def _send_email_verification_otp(user_id: int, email: str) -> None:
        """Generate and send email verification OTP"""
        # Generate 6-digit OTP
        otp = User.generate_otp(6)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.OTP_EXPIRE_MINUTES
        )

        await UserRepository.update_email_otp(user_id, otp, expires_at)

        await EmailService.send_email_otp(user_id, otp)

    @staticmethod
    async def verify_email(verify_data: VerifyEmailInput) -> str:
        """Verify email with OTP"""
        user = await UserRepository.get_by_email(verify_data.email)
        if not user:
            raise ValueError("User not found!")

        if user.is_active:
            raise ValueError("Email already verified!")

        # Checking if OTP matches and hasn't expired
        now = datetime.now(timezone.utc)
        if (
            not user.email_otp
            or user.email_otp != verify_data.otp
            or not user.email_otp_expires_at
            or user.email_otp_expires_at < now
        ):
            raise ValueError("Invalid or expired OTP!")

        await UserRepository.verify_email(user.id)

        await EmailService.send_account_verified(user.id)

        return "Email verified successfully! You can now log in."

    @staticmethod
    async def resend_email_otp(resend_data: ResendOTPInput) -> str:
        """Resend email verification OTP"""
        user = await UserRepository.get_by_email(resend_data.email)
        if not user:
            raise ValueError("User not found!")

        if user.is_active:
            raise ValueError("Email already verified!")

        if user.email_otp_expires_at and user.email_otp_expires_at > datetime.now(
            timezone.utc
        ) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES - 2):
            raise ValueError("Please wait before requesting a new OTP!")

        await AuthService._send_email_verification_otp(user.id, user.email)
        return "Verification code sent! Please check your email."

    @staticmethod
    async def forgot_password(forgot_data: ForgotPasswordInput) -> str:
        """Initiate password reset process"""
        user = await UserRepository.get_by_email(forgot_data.email)
        if not user:
            return "If the email exists, you'll receive password reset instructions."

        if not user.is_active:
            raise ValueError("Please verify your email first!")

        # Generate password reset OTP
        otp = User.generate_otp(6)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.OTP_EXPIRE_MINUTES
        )

        await UserRepository.update_password_reset_otp(user.id, otp, expires_at)
        await EmailService.send_forgot_password(user.id, otp)

        return "Password reset code sent to your email!"

    @staticmethod
    async def reset_password(reset_data: ResetPasswordInput) -> str:
        """Reset password with OTP"""
        user = await UserRepository.get_by_email(reset_data.email)
        if not user:
            raise ValueError("Invalid reset request!")

        now = datetime.now(timezone.utc)
        if (
            not user.password_reset_otp
            or user.password_reset_otp != reset_data.otp
            or not user.password_reset_otp_expires_at
            or user.password_reset_otp_expires_at < now
        ):
            raise ValueError("Invalid or expired reset code!")

        if len(reset_data.new_password) < 8:
            raise ValueError("Password must be at least 8 characters long!")

        new_password_hash = AuthService.get_password_hash(reset_data.new_password)
        await UserRepository.update_password(user.id, new_password_hash)

        await UserRepository.clear_password_reset_otp(user.id)

        await RefreshTokenRepository.delete_all_for_user(user.id)

        await EmailService.send_password_reset(user.id)

        return "Password reset successful! Please log in with your new password."

    @staticmethod
    async def change_password(change_data: ChangePasswordInput, user_id: int) -> str:
        """Change password for authenticated user"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found!")

        if not AuthService.verify_password(change_data.current_password, user.password):
            raise ValueError("Current password is incorrect!")

        if len(change_data.new_password) < 8:
            raise ValueError("New password must be at least 8 characters long!")

        if change_data.current_password == change_data.new_password:
            raise ValueError("New password must be different from current password!")

        new_password_hash = AuthService.get_password_hash(change_data.new_password)
        await UserRepository.update_password(user_id, new_password_hash)

        await RefreshTokenRepository.delete_all_for_user(user_id)

        return "Password changed successfully!"

    @staticmethod
    async def delete_account(user_id: int) -> str:
        """Soft delete user account"""
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found!")

        # Soft delete the account
        await UserRepository.deactivate_user(user_id)

        # Invalidate all refresh tokens
        await RefreshTokenRepository.delete_all_for_user(user_id)

        recovery_link = (
            f"{settings.FRONTEND_URL}/recover-account?token=recovery_token_here"
        )
        await EmailService.send_account_deleted(user_id, recovery_link)

        return (
            "Account deleted successfully. Check your email for recovery instructions."
        )

    # @staticmethod
    # async def get_admin_user(token: str) -> UserType:
    #     current_user = await AuthService.get_current_user(token)
    #     if current_user.role != "admin":
    #         raise ValueError("User is not an admin")
    #     return current_user
