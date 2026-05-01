"""Pydantic schemas for movies feature."""

from typing import Optional, List
from pydantic import BaseModel


# Genre schemas
class GenreBase(BaseModel):
    name: str


class GenreCreate(GenreBase):
    pass


class GenreResponse(GenreBase):
    id: int

    class Config:
        from_attributes = True


# Movie schemas
class MovieBase(BaseModel):
    title: str
    release_year: Optional[int] = None
    description: Optional[str] = None


class MovieCreate(MovieBase):
    genre_ids: Optional[List[int]] = None  # список ID жанров при создании


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    release_year: Optional[int] = None
    description: Optional[str] = None
    genre_ids: Optional[List[int]] = None


class MovieResponse(MovieBase):
    id: int
    created_at: Optional[str] = None
    genres: List[GenreResponse] = []

    class Config:
        from_attributes = True
