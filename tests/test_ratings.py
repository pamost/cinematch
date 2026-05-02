"""Tests for ratings endpoints and service layer."""

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.features.ratings.service import (
    get_rating_by_id,
    get_user_rating_for_movie,
    list_user_ratings,
    create_rating,
    update_rating,
    delete_rating,
)
from app.features.ratings.schemas import RatingCreate, RatingUpdate
from app.features.auth.service import create_user
from app.features.movies.service import create_movie
from app.features.movies.schemas import MovieCreate


class TestRatings:
    """Tests for rating endpoints."""

    async def _create_movie(self, client, headers):
        """Helper to create a movie and return its id."""
        resp = await client.post("/movies/", json={"title": "M"}, headers=headers)
        return resp.json()["id"]

    async def test_create_rating(self, client: AsyncClient, auth_headers: dict):
        """Create a new rating."""
        movie_id = await self._create_movie(client, auth_headers)
        resp = await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 4},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["rating"] == 4

    async def test_duplicate_rating(self, client: AsyncClient, auth_headers: dict):
        """Creating a duplicate rating returns 400."""
        movie_id = await self._create_movie(client, auth_headers)
        await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 3},
            headers=auth_headers,
        )
        resp = await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 5},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    async def test_get_my_ratings(self, client: AsyncClient, auth_headers: dict):
        """Get current user's ratings."""
        movie_id = await self._create_movie(client, auth_headers)
        await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 5},
            headers=auth_headers,
        )
        resp = await client.get("/ratings/my", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_update_rating(self, client: AsyncClient, auth_headers: dict):
        """Update an existing rating."""
        movie_id = await self._create_movie(client, auth_headers)
        create = await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 2},
            headers=auth_headers,
        )
        rating_id = create.json()["id"]
        resp = await client.put(
            f"/ratings/{rating_id}", json={"rating": 5}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["rating"] == 5

    async def test_update_rating_not_found(self, client: AsyncClient, auth_headers: dict):
        """Update non-existent rating returns 404."""
        resp = await client.put(
            "/ratings/9999", json={"rating": 3}, headers=auth_headers
        )
        assert resp.status_code == 404

    async def test_update_rating_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Update another user's rating returns 403."""
        await client.post(
            "/auth/register", json={"username": "other", "password": "p"}
        )
        other_token = (
            await client.post(
                "/auth/login", data={"username": "other", "password": "p"}
            )
        ).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        movie_id = await self._create_movie(client, auth_headers)
        create = await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 4},
            headers=auth_headers,
        )
        rating_id = create.json()["id"]

        resp = await client.put(
            f"/ratings/{rating_id}", json={"rating": 1}, headers=other_headers
        )
        assert resp.status_code == 403

    async def test_delete_rating(self, client: AsyncClient, auth_headers: dict):
        """Delete an existing rating."""
        movie_id = await self._create_movie(client, auth_headers)
        create = await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 3},
            headers=auth_headers,
        )
        rating_id = create.json()["id"]
        resp = await client.delete(f"/ratings/{rating_id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_delete_rating_not_found(self, client: AsyncClient, auth_headers: dict):
        """Delete non-existent rating returns 404."""
        resp = await client.delete("/ratings/9999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_delete_rating_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Delete another user's rating returns 403."""
        await client.post(
            "/auth/register", json={"username": "other2", "password": "p"}
        )
        other_token = (
            await client.post(
                "/auth/login", data={"username": "other2", "password": "p"}
            )
        ).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        movie_id = await self._create_movie(client, auth_headers)
        create = await client.post(
            "/ratings/",
            json={"movie_id": movie_id, "rating": 4},
            headers=auth_headers,
        )
        rating_id = create.json()["id"]

        resp = await client.delete(f"/ratings/{rating_id}", headers=other_headers)
        assert resp.status_code == 403


class TestRatingsService:
    """Direct service tests (bypass dependency_overrides)."""

    async def test_rating_crud_direct(self, db_session: AsyncSession):
        """Test rating CRUD operations directly."""
        # create user and movie
        user = await create_user(db_session, "ratinguser", "pass")
        movie_data = MovieCreate(title="Rating Movie")
        movie = await create_movie(db_session, movie_data)

        # create rating
        rating_data = RatingCreate(movie_id=movie.id, rating=4)
        rating = await create_rating(db_session, user.id, rating_data)
        assert rating.rating == 4
        assert rating.user_id == user.id
        assert rating.movie_id == movie.id

        # get by id
        found = await get_rating_by_id(db_session, rating.id)
        assert found is not None
        assert found.rating == 4

        # get by id not found
        found = await get_rating_by_id(db_session, 9999)
        assert found is None

        # get user rating for movie
        found = await get_user_rating_for_movie(db_session, user.id, movie.id)
        assert found is not None
        assert found.rating == 4

        # get user rating for movie not found
        found = await get_user_rating_for_movie(db_session, user.id, 9999)
        assert found is None

        # list user ratings
        ratings = await list_user_ratings(db_session, user.id)
        assert len(ratings) == 1

        # update rating
        update_data = RatingUpdate(rating=2)
        updated = await update_rating(db_session, rating.id, update_data)
        assert updated is not None
        assert updated.rating == 2

        # update not found
        updated = await update_rating(db_session, 9999, update_data)
        assert updated is None

        # delete rating
        deleted = await delete_rating(db_session, rating.id)
        assert deleted is True

        # delete not found
        deleted = await delete_rating(db_session, 9999)
        assert deleted is False
