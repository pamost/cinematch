"""Pydantic schemas for ratings feature."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class RatingBase(BaseModel):
    """Base schema for rating."""

    rating: int


class RatingCreate(RatingBase):  # pylint: disable=too-few-public-methods
    """Schema for creating a rating (requires movie_id)."""

    movie_id: int


class RatingUpdate(RatingBase):  # pylint: disable=too-few-public-methods
    """Schema for updating a rating (only rating field)."""


class RatingResponse(RatingBase):  # pylint: disable=too-few-public-methods
    """Schema for returning a rating."""

    id: int
    user_id: int
    movie_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
