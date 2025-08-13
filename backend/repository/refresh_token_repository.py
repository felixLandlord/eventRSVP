from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, delete
from backend.models.refresh_token_model import RefreshToken
from backend.core.database import async_session


class RefreshTokenRepository:
    @staticmethod
    async def create(user_id: int, token: str, expires_at: datetime):
        async with async_session() as session:
            refresh_token = RefreshToken(
                user_id=user_id, token=token, expires_at=expires_at
            )
            session.add(refresh_token)
            await session.commit()

    @staticmethod
    async def get(token: str) -> Optional[RefreshToken]:
        async with async_session() as session:
            result = await session.execute(
                select(RefreshToken).where(RefreshToken.token == token)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def delete(token: str):
        async with async_session() as session:
            await session.execute(
                delete(RefreshToken).where(RefreshToken.token == token)
            )
            await session.commit()

    @staticmethod
    async def delete_all_for_user(user_id: int):
        async with async_session() as session:
            await session.execute(
                delete(RefreshToken).where(RefreshToken.user_id == user_id)
            )
            await session.commit()

    @staticmethod
    async def get_active_token_for_user(user_id: int) -> Optional[RefreshToken]:
        async with async_session() as session:
            # Clean up expired tokens
            await session.execute(
                delete(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.expires_at <= datetime.now(timezone.utc),
                )
            )
            result = await session.execute(
                select(RefreshToken)
                .where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.expires_at > datetime.now(timezone.utc),
                )
                .order_by(RefreshToken.expires_at.desc())
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def invalidate_all_for_user(user_id: int):
        async with async_session() as session:
            await session.execute(
                delete(RefreshToken).where(RefreshToken.user_id == user_id)
            )
            await session.commit()
