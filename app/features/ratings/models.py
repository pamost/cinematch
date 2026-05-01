"""SQLModel models for ratings feature."""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class Rating(SQLModel, table=True):
    """User rating for a movie."""

    __tablename__ = "ratings"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    movie_id: int = Field(foreign_key="movies.id", nullable=False)
    rating: int = Field(ge=1, le=5, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
