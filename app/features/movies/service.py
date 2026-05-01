# app/features/movies/service.py

"""Business logic for movies feature."""

from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete
from app.features.movies.models import Movie, Genre, MovieGenre
from app.features.movies.schemas import MovieCreate, MovieUpdate


# ----- Genre operations -----
async def get_genre_by_id(session: AsyncSession, genre_id: int) -> Genre | None:
    """Retrieve a genre by its ID."""
    result = await session.exec(select(Genre).where(Genre.id == genre_id))
    return result.one_or_none()


async def get_genre_by_name(session: AsyncSession, name: str) -> Genre | None:
    """Retrieve a genre by its name."""
    result = await session.exec(select(Genre).where(Genre.name == name))
    return result.one_or_none()


async def create_genre(session: AsyncSession, name: str) -> Genre:
    """Create a new genre."""
    genre = Genre(name=name)
    session.add(genre)
    await session.commit()
    await session.refresh(genre)
    return genre


async def get_or_create_genre(session: AsyncSession, name: str) -> Genre:
    """Get existing genre by name, or create it if not found."""
    genre = await get_genre_by_name(session, name)
    if not genre:
        genre = await create_genre(session, name)
    return genre


async def list_genres(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Genre]:
    """Return list of genres with pagination."""
    result = await session.exec(select(Genre).offset(skip).limit(limit))
    return result.all()


# ----- Movie operations -----
async def get_movie_by_id(session: AsyncSession, movie_id: int) -> Movie | None:
    """Retrieve a movie by its ID, including its genres."""
    result = await session.exec(select(Movie).where(Movie.id == movie_id))
    movie = result.one_or_none()
    if movie:
        await session.refresh(movie, attribute_names=["genres"])
    return movie


async def list_movies(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    genre_id: Optional[int] = None
) -> List[Movie]:
    """Return list of movies with optional genre filter and pagination."""
    if genre_id:
        # Используем JOIN вместо in_ – так Pylint не ругается
        query = (
            select(Movie)
            .join(MovieGenre)
            .where(MovieGenre.genre_id == genre_id)
            .distinct()
            .offset(skip)
            .limit(limit)
        )
    else:
        query = select(Movie).offset(skip).limit(limit)
    result = await session.exec(query)
    movies = result.all()
    for movie in movies:
        await session.refresh(movie, attribute_names=["genres"])
    return movies

async def create_movie(session: AsyncSession, movie_data: MovieCreate) -> Movie:
    """Create a new movie and associate with genres if IDs provided."""
    movie = Movie(
        title=movie_data.title,
        release_year=movie_data.release_year,
        description=movie_data.description
    )
    session.add(movie)
    await session.commit()
    await session.refresh(movie)

    if movie_data.genre_ids:
        for genre_id in set(movie_data.genre_ids):
            genre = await get_genre_by_id(session, genre_id)
            if genre:
                session.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))
        await session.commit()
        await session.refresh(movie, attribute_names=["genres"])
    return movie


async def update_movie(
    session: AsyncSession,
    movie_id: int,
    movie_data: MovieUpdate
) -> Movie | None:
    """Update movie fields and genre associations."""
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        return None

    # Update scalar fields
    update_data = movie_data.model_dump(exclude_unset=True, exclude={"genre_ids"})
    for key, value in update_data.items():
        setattr(movie, key, value)

    # Update genres if provided
    if movie_data.genre_ids is not None:
        await session.exec(delete(MovieGenre).where(MovieGenre.movie_id == movie_id))
        for genre_id in set(movie_data.genre_ids):
            genre = await get_genre_by_id(session, genre_id)
            if genre:
                session.add(MovieGenre(movie_id=movie.id, genre_id=genre.id))

    session.add(movie)
    await session.commit()
    await session.refresh(movie, attribute_names=["genres"])
    return movie


async def delete_movie(session: AsyncSession, movie_id: int) -> bool:
    """Delete a movie and all its genre associations."""
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        return False
    await session.exec(delete(MovieGenre).where(MovieGenre.movie_id == movie_id))
    await session.delete(movie)
    await session.commit()
    return True
