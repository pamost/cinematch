"""API routes for ratings feature."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.auth import get_current_user
from app.features.auth.models import User
from app.features.ratings import service as rating_service
from app.features.ratings.schemas import (
    RatingCreate, RatingUpdate, RatingResponse
)

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(
    rating_data: RatingCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Rate a movie (1-5)."""
    # check if rating already exists
    existing = await rating_service.get_user_rating_for_movie(
        session, current_user.id, rating_data.movie_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already rated this movie"
        )
    rating = await rating_service.create_rating(
        session, current_user.id, rating_data
    )
    return rating


@router.get("/my", response_model=List[RatingResponse])
async def get_my_ratings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get all ratings made by the authenticated user."""
    ratings = await rating_service.list_user_ratings(
        session, current_user.id, skip, limit
    )
    return ratings


@router.put("/{rating_id}", response_model=RatingResponse)
async def update_rating(
    rating_id: int,
    rating_data: RatingUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update an existing rating."""
    rating = await rating_service.get_rating_by_id(session, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if rating.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own ratings"
        )
    updated = await rating_service.update_rating(session, rating_id, rating_data)
    return updated


@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    rating_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a rating."""
    rating = await rating_service.get_rating_by_id(session, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if rating.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own ratings"
        )
    await rating_service.delete_rating(session, rating_id)
