"""Tests for recommendations endpoints and service layer."""

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.features.recommendations.service import (
    get_user_ratings,
    get_all_users_ratings,
    pearson_correlation,
    get_most_popular_movies,
    _get_similar_users_from_ratings,
    _compute_predictions,
    get_top_n_recommendations,
)
from app.features.recommendations.router import get_recommendations
from app.features.auth.service import create_user
from app.features.movies.service import create_movie
from app.features.movies.schemas import MovieCreate
from app.features.ratings.service import create_rating
from app.features.ratings.schemas import RatingCreate


class TestRecommendations:
    """Tests for recommendations endpoints."""

    async def test_get_recommendations(self, client: AsyncClient, auth_headers: dict):
        """Get recommendations returns a list (empty initially)."""
        resp = await client.get("/recommendations/", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_recommendations_with_data(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Get recommendations with rating data returns results."""
        # Create a second user with ratings
        await client.post(
            "/auth/register", json={"username": "other", "password": "p"}
        )
        other_token = (
            await client.post(
                "/auth/login", data={"username": "other", "password": "p"}
            )
        ).json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Create movies
        m1 = (
            await client.post(
                "/movies/", json={"title": "Movie 1"}, headers=auth_headers
            )
        ).json()["id"]
        m2 = (
            await client.post(
                "/movies/", json={"title": "Movie 2"}, headers=auth_headers
            )
        ).json()["id"]
        m3 = (
            await client.post(
                "/movies/", json={"title": "Movie 3"}, headers=auth_headers
            )
        ).json()["id"]

        # Rate movies by both users
        for mid in [m1, m2, m3]:
            await client.post(
                "/ratings/",
                json={"movie_id": mid, "rating": 5},
                headers=auth_headers,
            )
            await client.post(
                "/ratings/",
                json={"movie_id": mid, "rating": 4},
                headers=other_headers,
            )

        # User has >=3 ratings — collaborative filtering should work
        resp = await client.get("/recommendations/?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestRecommendationsService:
    """Direct service tests (bypass dependency_overrides)."""

    async def test_get_user_ratings_empty(self, db_session: AsyncSession):
        """get_user_ratings returns empty dict for non-existent user."""
        ratings = await get_user_ratings(db_session, 1)
        assert ratings == {}

    async def test_get_all_users_ratings_empty(self, db_session: AsyncSession):
        """get_all_users_ratings returns empty dict with no data."""
        ratings = await get_all_users_ratings(db_session)
        assert ratings == {}

    async def test_pearson_correlation(self):
        """Pearson correlation returns a float for valid inputs."""
        r1 = {1: 5.0, 2: 3.0, 3: 4.0}
        r2 = {1: 4.0, 2: 2.0, 3: 5.0}
        corr = pearson_correlation(r1, r2)
        assert isinstance(corr, float)

    async def test_pearson_correlation_less_than_2_common(self):
        """Pearson correlation returns 0.0 with fewer than 2 common items."""
        r1 = {1: 5.0}
        r2 = {2: 4.0}
        corr = pearson_correlation(r1, r2)
        assert corr == 0.0

    async def test_get_most_popular_movies_empty(self, db_session: AsyncSession):
        """get_most_popular_movies returns empty list with no data."""
        movies = await get_most_popular_movies(db_session, 5)
        assert movies == []

    async def test_get_most_popular_movies_with_data(self, db_session: AsyncSession):
        """get_most_popular_movies returns movies with ratings."""
        user = await create_user(db_session, "recuser", "pass")
        movie_data = MovieCreate(title="Popular Movie")
        movie = await create_movie(db_session, movie_data)
        rating_data = RatingCreate(movie_id=movie.id, rating=5)
        await create_rating(db_session, user.id, rating_data)

        movies = await get_most_popular_movies(db_session, 5)
        assert len(movies) == 1
        assert movies[0].title == "Popular Movie"

    async def test_get_similar_users(self):
        """_get_similar_users_from_ratings finds similar users."""
        user_ratings = {1: 5.0, 2: 3.0}
        all_ratings = {
            1: {1: 5.0, 2: 3.0},
            2: {1: 4.0, 2: 2.0, 3: 5.0},
        }
        similar = _get_similar_users_from_ratings(1, user_ratings, all_ratings, 0.0, 5)
        assert len(similar) == 1
        assert similar[0][0] == 2

    async def test_compute_predictions(self):
        """_compute_predictions generates predictions for unseen movies."""
        user_ratings = {1: 5.0}
        all_ratings = {
            1: {1: 5.0},
            2: {1: 4.0, 2: 3.0, 3: 5.0},
        }
        similar_users = [(2, 0.8)]
        predictions = await _compute_predictions(
            user_ratings, all_ratings, similar_users
        )
        assert 2 in predictions
        assert 3 in predictions

    async def test_get_top_n_recommendations_less_than_3_ratings(
        self, db_session: AsyncSession
    ):
        """get_top_n_recommendations falls back to popular with <3 ratings."""
        user = await create_user(db_session, "recuser2", "pass")
        movie_data = MovieCreate(title="Rec Movie")
        movie = await create_movie(db_session, movie_data)
        rating_data = RatingCreate(movie_id=movie.id, rating=5)
        await create_rating(db_session, user.id, rating_data)

        recs = await get_top_n_recommendations(db_session, user.id, n=5)
        assert isinstance(recs, list)

    async def test_get_top_n_recommendations_with_data(
        self, db_session: AsyncSession
    ):
        """get_top_n_recommendations returns collaborative recommendations."""
        # Create two users
        user1 = await create_user(db_session, "recuser3", "pass")
        user2 = await create_user(db_session, "recuser4", "pass")

        # Create movies
        m1 = await create_movie(db_session, MovieCreate(title="Movie A"))
        m2 = await create_movie(db_session, MovieCreate(title="Movie B"))
        m3 = await create_movie(db_session, MovieCreate(title="Movie C"))
        m4 = await create_movie(db_session, MovieCreate(title="Movie D"))

        # Both users rate same movies with varied ratings
        await create_rating(
            db_session, user1.id, RatingCreate(movie_id=m1.id, rating=5)
        )
        await create_rating(
            db_session, user1.id, RatingCreate(movie_id=m2.id, rating=4)
        )
        await create_rating(
            db_session, user1.id, RatingCreate(movie_id=m3.id, rating=3)
        )
        await create_rating(
            db_session, user2.id, RatingCreate(movie_id=m1.id, rating=5)
        )
        await create_rating(
            db_session, user2.id, RatingCreate(movie_id=m2.id, rating=4)
        )
        await create_rating(
            db_session, user2.id, RatingCreate(movie_id=m3.id, rating=3)
        )

        # user2 also rates an extra movie — should be recommended to user1
        await create_rating(
            db_session, user2.id, RatingCreate(movie_id=m4.id, rating=5)
        )

        # user1 has >=3 ratings, should trigger collaborative filtering
        recs = await get_top_n_recommendations(db_session, user1.id, n=5)
        assert isinstance(recs, list)
        assert len(recs) > 0

    async def test_get_top_n_recommendations_no_similar_users(
        self, db_session: AsyncSession
    ):
        """User has >=3 ratings but no similar users exist."""
        user = await create_user(db_session, "lonelyuser", "pass")
        m1 = await create_movie(db_session, MovieCreate(title="M1"))
        m2 = await create_movie(db_session, MovieCreate(title="M2"))
        m3 = await create_movie(db_session, MovieCreate(title="M3"))
        await create_rating(
            db_session, user.id, RatingCreate(movie_id=m1.id, rating=5)
        )
        await create_rating(
            db_session, user.id, RatingCreate(movie_id=m2.id, rating=4)
        )
        await create_rating(
            db_session, user.id, RatingCreate(movie_id=m3.id, rating=3)
        )

        recs = await get_top_n_recommendations(db_session, user.id, n=5)
        assert isinstance(recs, list)

    async def test_get_top_n_recommendations_no_predictions(
        self, db_session: AsyncSession
    ):
        """Similar users exist but they rated the same movies — no new predictions."""
        user1 = await create_user(db_session, "user_a", "pass")
        user2 = await create_user(db_session, "user_b", "pass")
        m1 = await create_movie(db_session, MovieCreate(title="X1"))
        m2 = await create_movie(db_session, MovieCreate(title="X2"))
        m3 = await create_movie(db_session, MovieCreate(title="X3"))
        await create_rating(
            db_session, user1.id, RatingCreate(movie_id=m1.id, rating=5)
        )
        await create_rating(
            db_session, user1.id, RatingCreate(movie_id=m2.id, rating=4)
        )
        await create_rating(
            db_session, user1.id, RatingCreate(movie_id=m3.id, rating=3)
        )
        await create_rating(
            db_session, user2.id, RatingCreate(movie_id=m1.id, rating=5)
        )
        await create_rating(
            db_session, user2.id, RatingCreate(movie_id=m2.id, rating=4)
        )
        await create_rating(
            db_session, user2.id, RatingCreate(movie_id=m3.id, rating=3)
        )

        recs = await get_top_n_recommendations(db_session, user1.id, n=5)
        assert isinstance(recs, list)

    async def test_get_recommendations_direct(self, db_session: AsyncSession):
        """Direct call to get_recommendations router function."""
        user = await create_user(db_session, "directuser", "pass")
        result = await get_recommendations(
            limit=5, session=db_session, current_user=user
        )
        assert isinstance(result, list)
