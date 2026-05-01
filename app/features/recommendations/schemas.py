"""Pydantic schemas for recommendations feature."""

from typing import List, Optional
from pydantic import BaseModel


class RecommendedMovie(BaseModel):
    """Schema for a single movie recommendation."""
    id: int
    title: str
    predicted_rating: Optional[float] = None
    reason: Optional[str] = None  # e.g., "popular", "collaborative"


class RecommendationResponse(BaseModel):
    """Response schema for recommendations endpoint."""
    recommendations: List[RecommendedMovie]
