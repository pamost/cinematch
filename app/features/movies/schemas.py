"""Pydantic schemas for movies feature."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# Genre schemas
class GenreBase(BaseModel):
    """Base schema for genre."""

    name: str


class GenreCreate(GenreBase):
    """Schema for creating a genre."""


class GenreUpdate(BaseModel):
    """Schema for updating a genre."""

    name: str


class GenreResponse(GenreBase):
    """Schema for returning a genre."""

    id: int

    model_config = ConfigDict(from_attributes=True)


# Movie schemas
class MovieBase(BaseModel):
    """Base schema for movie."""

    title: str
    release_year: Optional[int] = None
    description: Optional[str] = None


class MovieCreate(MovieBase):
    """Schema for creating a movie with optional genre IDs."""

    genre_ids: Optional[List[int]] = None


class MovieUpdate(BaseModel):
    """Schema for updating a movie (all fields optional)."""

    title: Optional[str] = None
    release_year: Optional[int] = None
    description: Optional[str] = None
    genre_ids: Optional[List[int]] = None


class MovieResponse(MovieBase):
    """Schema for returning a movie with genres and creation timestamp."""

    id: int
    created_at: Optional[datetime] = None
    genres: List[GenreResponse] = []

    model_config = ConfigDict(from_attributes=True)
