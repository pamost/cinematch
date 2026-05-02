"""Pytest fixtures for CineMatch tests.

Automatically creates and drops a test database (cinematch_test).
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.main import app
from app.core.config import settings
from app.core.database import get_session
from app.core.auth import get_password_hash, create_access_token
from app.features.auth.models import User

TEST_DB_NAME = "cinematch_test"

# Engine without database — to create/drop test DB
admin_engine = create_async_engine(
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/postgres",
    echo=False,
    future=True,
    poolclass=NullPool,
)

# Engine connected to the test database
TEST_DB_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{TEST_DB_NAME}"
)
test_engine = create_async_engine(
    TEST_DB_URL, echo=False, future=True, poolclass=NullPool,
)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _create_test_database():
    """Create the test database if it does not exist."""
    async with admin_engine.connect() as conn:
        await conn.execute(text("COMMIT"))
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
        )
        if not result.scalar():
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))


async def _drop_test_database():
    """Drop the test database."""
    # Close the test engine so no connections remain
    await test_engine.dispose()
    # Terminate any remaining connections to the test database
    async with admin_engine.connect() as conn:
        await conn.execute(text("COMMIT"))
        await conn.execute(text(
            f"SELECT pg_terminate_backend(pg_stat_activity.pid) "
            f"FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{TEST_DB_NAME}' "
            f"AND pid <> pg_backend_pid()"
        ))
    # Now drop the database
    async with admin_engine.connect() as conn:
        await conn.execute(text("COMMIT"))
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))


async def _create_tables():
    """Create all tables in the test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def _prepare():
    """Create test database and tables once before all tests."""
    asyncio.run(_create_test_database())
    asyncio.run(_create_tables())
    yield
    asyncio.run(_drop_test_database())


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Clean all tables before each test."""
    async with test_engine.begin() as conn:
        for table in reversed(SQLModel.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE {table.name} CASCADE"))


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client for testing endpoints."""

    async def _get_session():
        async with TestAsyncSessionLocal() as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for direct service calls."""
    async with TestAsyncSessionLocal() as s:
        yield s


@pytest_asyncio.fixture
async def auth_headers(db_session: AsyncSession) -> dict:  # pylint: disable=redefined-outer-name
    """Create a user and return authorization headers with a JWT token."""
    hashed = get_password_hash("testpass123")
    user = User(username="testuser", hashed_password=hashed)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}
