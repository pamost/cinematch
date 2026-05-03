"""Database engine and session dependency.

Схема БД управляется через Alembic (alembic upgrade head).
"""

from typing import AsyncGenerator
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
ASYNC_SESSION_LOCAL = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with ASYNC_SESSION_LOCAL() as session:
        yield session
