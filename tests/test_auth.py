"""Tests for authentication endpoints and service layer."""

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.auth import get_current_user, create_access_token
from app.features.auth.service import (
    get_user_by_username,
    get_user_by_id,
    create_user,
    authenticate_user,
)


class TestRegister:
    """Tests for user registration endpoint."""

    async def test_success(self, client: AsyncClient):
        """Register a new user successfully."""
        resp = await client.post(
            "/auth/register", json={"username": "new", "password": "pass"}
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "new"

    async def test_duplicate(self, client: AsyncClient):
        """Registering with an existing username returns 400."""
        await client.post(
            "/auth/register", json={"username": "dup", "password": "pass"}
        )
        resp = await client.post(
            "/auth/register", json={"username": "dup", "password": "pass"}
        )
        assert resp.status_code == 400


class TestLogin:
    """Tests for user login endpoint."""

    async def test_success(self, client: AsyncClient):
        """Login with valid credentials returns a token."""
        await client.post(
            "/auth/register", json={"username": "loguser", "password": "secret"}
        )
        resp = await client.post(
            "/auth/login", data={"username": "loguser", "password": "secret"}
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_wrong_password(self, client: AsyncClient):
        """Login with wrong password returns 401."""
        await client.post(
            "/auth/register", json={"username": "wpuser", "password": "secret"}
        )
        resp = await client.post(
            "/auth/login", data={"username": "wpuser", "password": "wrong"}
        )
        assert resp.status_code == 401

    async def test_nonexistent_user(self, client: AsyncClient):
        """Login with non-existent user returns 401."""
        resp = await client.post(
            "/auth/login", data={"username": "nobody", "password": "x"}
        )
        assert resp.status_code == 401


class TestAuthService:
    """Tests for auth service layer and token validation."""

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Request with invalid token returns 401."""
        resp = await client.get(
            "/movies/genres", headers={"Authorization": "Bearer invalid"}
        )
        assert resp.status_code == 401

    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Request without token returns 401."""
        resp = await client.get("/movies/genres")
        assert resp.status_code == 401

    async def test_get_user_by_username_not_found(self, db_session: AsyncSession):
        """get_user_by_username returns None for non-existent user."""
        user = await get_user_by_username(db_session, "nonexistent")
        assert user is None

    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """get_user_by_id returns None for non-existent user."""
        user = await get_user_by_id(db_session, 9999)
        assert user is None

    async def test_create_and_get_user_direct(self, db_session: AsyncSession):
        """Create a user and retrieve it by username and id."""
        user = await create_user(db_session, "testuser", "password")
        assert user.username == "testuser"
        assert user.id is not None

        found = await get_user_by_username(db_session, "testuser")
        assert found is not None
        assert found.id == user.id

        found_by_id = await get_user_by_id(db_session, user.id)
        assert found_by_id is not None
        assert found_by_id.username == "testuser"

    async def test_authenticate_user_success_direct(self, db_session: AsyncSession):
        """authenticate_user returns user for valid credentials."""
        await create_user(db_session, "authuser", "secret")
        user = await authenticate_user(db_session, "authuser", "secret")
        assert user is not None
        assert user.username == "authuser"

    async def test_authenticate_user_wrong_password_direct(
        self, db_session: AsyncSession
    ):
        """authenticate_user returns None for wrong password."""
        await create_user(db_session, "authuser2", "secret")
        user = await authenticate_user(db_session, "authuser2", "wrong")
        assert user is None

    async def test_authenticate_user_nonexistent_direct(self, db_session: AsyncSession):
        """authenticate_user returns None for non-existent user."""
        user = await authenticate_user(db_session, "nobody", "x")
        assert user is None

    async def test_get_current_user_nonexistent_user(self, client: AsyncClient):
        """Token with valid format but non-existent user ID returns 401."""
        token = create_access_token(data={"sub": "99999"})
        resp = await client.get(
            "/movies/genres", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 401

    async def test_get_current_user_direct_invalid_token(
        self, db_session: AsyncSession
    ):
        """Direct call to get_current_user with invalid token raises 401."""
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token="invalid-token", session=db_session)
        assert exc.value.status_code == 401

    async def test_get_current_user_direct_nonexistent_user(
        self, db_session: AsyncSession
    ):
        """Direct call with valid token but non-existent user raises 401."""
        token = create_access_token(data={"sub": "99999"})
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token=token, session=db_session)
        assert exc.value.status_code == 401

    async def test_get_current_user_direct_success(self, db_session: AsyncSession):
        """Direct call with valid token returns the user."""
        user = await create_user(db_session, "validuser", "pass")
        token = create_access_token(data={"sub": str(user.id)})
        result = await get_current_user(token=token, session=db_session)
        assert result.id == user.id
        assert result.username == "validuser"

    async def test_get_current_user_direct_no_sub(self, db_session: AsyncSession):
        """Direct call with token missing 'sub' claim raises 401."""
        token = create_access_token(data={"other": "value"})
        with pytest.raises(HTTPException) as exc:
            await get_current_user(token=token, session=db_session)
        assert exc.value.status_code == 401

    async def test_root_endpoint(self, client: AsyncClient):
        """Test the root endpoint returns welcome message."""
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"message": "CineMatch API"}
