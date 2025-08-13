from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from backend.models.base_model import Base
from backend.core.config import settings
from tenacity import retry, stop_after_attempt, wait_fixed

DATABASE_URL: str = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DATABASE}"
)


class DatabaseSession:
    def __init__(self, url: str = DATABASE_URL):
        self.engine = create_async_engine(
            url, echo=True, future=True, pool_size=5, max_overflow=10, pool_timeout=30
        )
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def create_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self):
        await self.engine.dispose()

    async def __aenter__(self) -> AsyncSession:
        self.session = self.SessionLocal()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def commit_rollback(self):
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise


db: DatabaseSession = DatabaseSession()

async_session: async_sessionmaker = db.SessionLocal
