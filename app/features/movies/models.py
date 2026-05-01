"""SQLModel models for movies feature."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


# 1. Сначала определяем промежуточную таблицу (link model)
class MovieGenre(SQLModel, table=True):
    """Many-to-many link between movies and genres."""
    __tablename__ = "movie_genres"
    movie_id: int = Field(foreign_key="movies.id", primary_key=True)
    genre_id: int = Field(foreign_key="genres.id", primary_key=True)


# 2. Затем модель Movie (с прямой ссылкой на MovieGenre)
class Movie(SQLModel, table=True):
    __tablename__ = "movies"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=255)
    release_year: Optional[int] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Связь с жанрами (используем класс MovieGenre, а не строку)
    genres: List["Genre"] = Relationship(back_populates="movies", link_model=MovieGenre)


# 3. Затем модель Genre (тоже с прямой ссылкой)
class Genre(SQLModel, table=True):
    __tablename__ = "genres"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)

    movies: List["Movie"] = Relationship(back_populates="genres", link_model=MovieGenre)
