"""Business logic for authentication feature."""

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.features.auth.models import User
from app.core.auth import get_password_hash, verify_password


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Retrieve user by username."""
    result = await session.exec(select(User).where(User.username == username))
    return result.one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """Retrieve user by ID."""
    result = await session.exec(select(User).where(User.id == user_id))
    return result.one_or_none()


async def create_user(session: AsyncSession, username: str, password: str) -> User:
    """Create new user with hashed password."""
    hashed = get_password_hash(password)
    user = User(username=username, hashed_password=hashed)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, username: str, password: str) -> User | None:
    """Verify username and password."""
    user = await get_user_by_username(session, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
