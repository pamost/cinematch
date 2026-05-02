"""Tests for movies endpoints and service layer."""

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.features.movies.service import (
    get_genre_by_id,
    get_genre_by_name,
    create_genre,
    get_or_create_genre,
    list_genres,
    get_movie_by_id,
    list_movies,
    create_movie,
    update_movie,
    delete_movie,
)
from app.features.movies.schemas import MovieCreate, MovieUpdate


class TestGenres:
    """Tests for genre endpoints."""

    async def test_list_genres(self, client: AsyncClient, auth_headers: dict):
        """List genres returns empty list initially."""
        resp = await client.get("/movies/genres", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_create_genre(self, client: AsyncClient, auth_headers: dict):
        """Create a new genre."""
        resp = await client.post(
            "/movies/genres", json={"name": "Action"}, headers=auth_headers
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Action"

    async def test_create_duplicate_genre(self, client: AsyncClient, auth_headers: dict):
        """Creating a duplicate genre returns 400."""
        await client.post(
            "/movies/genres", json={"name": "Drama"}, headers=auth_headers
        )
        resp = await client.post(
            "/movies/genres", json={"name": "Drama"}, headers=auth_headers
        )
        assert resp.status_code == 400


class TestMovies:
    """Tests for movie endpoints."""

    async def test_create_movie(self, client: AsyncClient, auth_headers: dict):
        """Create a new movie."""
        resp = await client.post(
            "/movies/", json={"title": "Test"}, headers=auth_headers
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == "Test"

    async def test_list_movies(self, client: AsyncClient, auth_headers: dict):
        """List movies returns created movies."""
        await client.post("/movies/", json={"title": "A"}, headers=auth_headers)
        resp = await client.get("/movies/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_get_movie(self, client: AsyncClient, auth_headers: dict):
        """Get a movie by id."""
        create = await client.post(
            "/movies/", json={"title": "B"}, headers=auth_headers
        )
        movie_id = create.json()["id"]
        resp = await client.get(f"/movies/{movie_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "B"

    async def test_get_movie_not_found(self, client: AsyncClient, auth_headers: dict):
        """Get non-existent movie returns 404."""
        resp = await client.get("/movies/9999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_update_movie(self, client: AsyncClient, auth_headers: dict):
        """Update a movie title."""
        create = await client.post(
            "/movies/", json={"title": "C"}, headers=auth_headers
        )
        movie_id = create.json()["id"]
        resp = await client.put(
            f"/movies/{movie_id}", json={"title": "Updated"}, headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"

    async def test_delete_movie(self, client: AsyncClient, auth_headers: dict):
        """Delete a movie."""
        create = await client.post(
            "/movies/", json={"title": "D"}, headers=auth_headers
        )
        movie_id = create.json()["id"]
        resp = await client.delete(f"/movies/{movie_id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_create_movie_with_genres(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Create a movie with genre associations."""
        g = await client.post(
            "/movies/genres", json={"name": "Sci-Fi"}, headers=auth_headers
        )
        gid = g.json()["id"]
        resp = await client.post(
            "/movies/",
            json={"title": "E", "genre_ids": [gid]},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert len(resp.json()["genres"]) == 1

    async def test_filter_movies_by_genre(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Filter movies by genre id."""
        g = await client.post(
            "/movies/genres", json={"name": "Comedy"}, headers=auth_headers
        )
        gid = g.json()["id"]
        await client.post(
            "/movies/",
            json={"title": "F", "genre_ids": [gid]},
            headers=auth_headers,
        )
        resp = await client.get(f"/movies/?genre_id={gid}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestMoviesService:
    """Direct service tests (bypass dependency_overrides)."""

    async def test_genre_crud_direct(self, db_session: AsyncSession):
        """Test genre CRUD operations directly."""
        # create
        genre = await create_genre(db_session, "Action")
        assert genre.name == "Action"
        assert genre.id is not None

        # get by id
        found = await get_genre_by_id(db_session, genre.id)
        assert found is not None
        assert found.name == "Action"

        # get by name
        found = await get_genre_by_name(db_session, "Action")
        assert found is not None

        # get by name not found
        found = await get_genre_by_name(db_session, "Nonexistent")
        assert found is None

        # get by id not found
        found = await get_genre_by_id(db_session, 9999)
        assert found is None

        # get or create existing
        g = await get_or_create_genre(db_session, "Action")
        assert g.id == genre.id

        # get or create new
        g = await get_or_create_genre(db_session, "Comedy")
        assert g.name == "Comedy"

        # list genres
        genres = await list_genres(db_session)
        assert len(genres) == 2

    async def test_movie_crud_direct(self, db_session: AsyncSession):
        """Test movie CRUD operations directly."""
        # create movie without genres
        movie_data = MovieCreate(title="Test Movie")
        movie = await create_movie(db_session, movie_data)
        assert movie.title == "Test Movie"
        assert movie.id is not None

        # get by id
        found = await get_movie_by_id(db_session, movie.id)
        assert found is not None
        assert found.title == "Test Movie"

        # get by id not found
        found = await get_movie_by_id(db_session, 9999)
        assert found is None

        # list movies
        movies = await list_movies(db_session)
        assert len(movies) == 1

        # update movie
        update_data = MovieUpdate(title="Updated Movie")
        updated = await update_movie(db_session, movie.id, update_data)
        assert updated is not None
        assert updated.title == "Updated Movie"

        # update not found
        updated = await update_movie(db_session, 9999, update_data)
        assert updated is None

        # delete movie
        deleted = await delete_movie(db_session, movie.id)
        assert deleted is True

        # delete not found
        deleted = await delete_movie(db_session, 9999)
        assert deleted is False

    async def test_movie_with_genres_direct(self, db_session: AsyncSession):
        """Test movie genre associations directly."""
        genre = await create_genre(db_session, "Sci-Fi")
        movie_data = MovieCreate(title="Sci-Fi Movie", genre_ids=[genre.id])
        movie = await create_movie(db_session, movie_data)
        assert len(movie.genres) == 1
        assert movie.genres[0].name == "Sci-Fi"

        # list with genre filter
        movies = await list_movies(db_session, genre_id=genre.id)
        assert len(movies) == 1

        # update genres
        genre2 = await create_genre(db_session, "Drama")
        update_data = MovieUpdate(genre_ids=[genre2.id])
        updated = await update_movie(db_session, movie.id, update_data)
        assert updated is not None
        assert len(updated.genres) == 1
        assert updated.genres[0].name == "Drama"
