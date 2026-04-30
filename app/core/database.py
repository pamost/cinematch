"""Database engine and session dependency."""

from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

# Асинхронный движок для подключения к БД
engine = create_async_engine(
    settings.database_url,
    echo=True,
    future=True
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables (for development only)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
