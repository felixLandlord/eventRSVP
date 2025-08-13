from backend.models.user_model import User
from backend.core.database import db
from sqlalchemy.sql import select, update as sql_update, delete as sql_delete

from typing import Optional, List
from backend.schemas.user_schema import UserCreate, UserUpdate
from datetime import datetime, timezone


class UserRepository:

    @staticmethod
    async def create(user_data: UserCreate) -> User:
        async with db as session:
            user = User(**user_data.model_dump())
            session.add(user)
            await db.commit_rollback()
            await session.refresh(user)
            return user

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        async with db as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        async with db as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            return result.scalars().first()

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 100) -> List[User]:
        async with db as session:
            stmt = select(User).offset(skip).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def update(user_id: int, user_data: UserUpdate) -> Optional[User]:
        async with db as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user:
                return None

            # Update user fields
            for field, value in user_data.model_dump(exclude_unset=True).items():
                if hasattr(user, field) and value is not None:
                    setattr(user, field, value)

            await db.commit_rollback()
            await session.refresh(user)
            return user

    @staticmethod
    async def delete(user_id: int) -> bool:
        async with db as session:
            stmt = sql_delete(User).where(User.id == user_id)
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def update_avatar(user_id: int, avatar_url: str) -> bool:
        async with db as session:
            stmt = sql_update(User).where(User.id == user_id).values(avatar=avatar_url)
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def activate_user(user_id: int) -> bool:
        async with db as session:
            stmt = (
                sql_update(User)
                .where(User.id == user_id)
                .values(is_active=True, is_deleted=False)
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def deactivate_user(user_id: int) -> bool:
        async with db as session:
            stmt = (
                sql_update(User)
                .where(User.id == user_id)
                .values(
                    is_active=False,
                    is_deleted=True,
                    deleted_at=datetime.now(timezone.utc),
                )
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def update_email_otp(user_id: int, otp: str, expires_at: datetime) -> bool:
        """Update email OTP and expiration"""
        async with db as session:
            stmt = (
                sql_update(User)
                .where(User.id == user_id)
                .values(email_otp=otp, email_otp_expires_at=expires_at)
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def verify_email(user_id: int) -> bool:
        """Mark email as verified and clear OTP"""
        async with db as session:
            stmt = (
                sql_update(User)
                .where(User.id == user_id)
                .values(
                    is_active=True,  # Activate user after email verification
                    email_otp=None,
                    email_otp_expires_at=None,
                )
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def update_password_reset_otp(
        user_id: int, otp: str, expires_at: datetime
    ) -> bool:
        """Update password reset OTP and expiration"""
        async with db as session:
            stmt = (
                sql_update(User)
                .where(User.id == user_id)
                .values(
                    password_reset_otp=otp, password_reset_otp_expires_at=expires_at
                )
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def clear_password_reset_otp(user_id: int) -> bool:
        """Clear password reset OTP after successful reset"""
        async with db as session:
            stmt = (
                sql_update(User)
                .where(User.id == user_id)
                .values(password_reset_otp=None, password_reset_otp_expires_at=None)
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0

    @staticmethod
    async def update_password(user_id: int, new_password_hash: str) -> bool:
        """Update user password"""
        async with db as session:
            stmt = (
                sql_update(User)
                .where(User.id == user_id)
                .values(password=new_password_hash)
            )
            result = await session.execute(stmt)
            await db.commit_rollback()
            return result.rowcount > 0
