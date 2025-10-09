from contextlib import asynccontextmanager
from typing import Callable, TypeVar, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from functools import wraps
from backend.core.logger import get_logger

logger = get_logger("db_session")

T = TypeVar("T")

class DatabaseSessionManager:
    """Async database session manager"""
    
    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self.session_factory = session_factory
        self.session: AsyncSession = None

    async def __aenter__(self) -> AsyncSession:
        """Enter the context manager, creating a new session"""
        self.session = self.session_factory()
        logger.debug("Database session created")
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager, handling commit/rollback"""
        try:
            if exc_type is not None:
                logger.warning(f"Rolling back transaction due to: {exc_type.__name__}")
                await self.session.rollback()
            else:
                logger.debug("Committing transaction")
                await self.session.commit()
        finally:
            logger.debug("Closing database session")
            await self.session.close()


def transaction_context(isolation_level: str = None):
    """
    Decorator for managing database transactions
    
    Args:
        isolation_level: Optional SQLAlchemy isolation level
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from backend.core.db.base import async_session_factory
            
            async with DatabaseSessionManager(async_session_factory) as session:
                if isolation_level:
                    await session.connection(execution_options={"isolation_level": isolation_level})
                return await func(*args, session=session, **kwargs)
        return wrapper
    return decorator