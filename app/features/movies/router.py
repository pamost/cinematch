# app/features/movies/router.py

"""API routes for movies feature."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.auth import get_current_user
from app.features.auth.models import User
from app.features.movies import service as movie_service
from app.features.movies.schemas import (
    MovieCreate, MovieUpdate, MovieResponse,
    GenreCreate, GenreUpdate, GenreResponse
)

router = APIRouter(prefix="/movies", tags=["movies"])


# ----- Genre endpoints -----
@router.get("/genres", response_model=List[GenreResponse])
async def list_genres(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)  # авторизация
):
    """Get list of genres with pagination."""
    genres = await movie_service.list_genres(session, skip, limit)
    return genres


@router.post("/genres", response_model=GenreResponse, status_code=status.HTTP_201_CREATED)
async def create_genre(
    genre_data: GenreCreate,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Create a new genre."""
    existing = await movie_service.get_genre_by_name(session, genre_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Genre already exists")
    genre = await movie_service.create_genre(session, genre_data.name)
    return genre


@router.put("/genres/{genre_id}", response_model=GenreResponse)
async def update_genre(
    genre_id: int,
    genre_data: GenreUpdate,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Update an existing genre."""
    existing = await movie_service.get_genre_by_name(session, genre_data.name)
    if existing and existing.id != genre_id:
        raise HTTPException(status_code=400, detail="Genre name already taken")
    genre = await movie_service.update_genre(session, genre_id, genre_data.name)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre


@router.delete("/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genre(
    genre_id: int,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Delete a genre."""
    deleted = await movie_service.delete_genre(session, genre_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Genre not found")


# ----- Movie endpoints -----
@router.get("/", response_model=List[MovieResponse])
async def list_movies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    genre_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Get list of movies with optional genre filter and pagination."""
    movies = await movie_service.list_movies(session, skip, limit, genre_id)
    return movies


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Get detailed information about a movie."""
    movie = await movie_service.get_movie_by_id(session, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
async def create_movie(
    movie_data: MovieCreate,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Create a new movie with optional genre associations."""
    return await movie_service.create_movie(session, movie_data)


@router.put("/{movie_id}", response_model=MovieResponse)
async def update_movie(
    movie_id: int,
    movie_data: MovieUpdate,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Update an existing movie."""
    movie = await movie_service.update_movie(session, movie_id, movie_data)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(
    movie_id: int,
    session: AsyncSession = Depends(get_session),
    _user: User = Depends(get_current_user)
):
    """Delete a movie."""
    deleted = await movie_service.delete_movie(session, movie_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Movie not found")
