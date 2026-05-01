"""Business logic for ratings feature."""

from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete
from app.features.ratings.models import Rating
from app.features.ratings.schemas import RatingCreate, RatingUpdate


async def get_rating_by_id(session: AsyncSession, rating_id: int) -> Rating | None:
    """Retrieve a rating by its ID."""
    result = await session.exec(select(Rating).where(Rating.id == rating_id))
    return result.one_or_none()


async def get_user_rating_for_movie(
    session: AsyncSession,
    user_id: int,
    movie_id: int
) -> Rating | None:
    """Retrieve a specific user's rating for a specific movie."""
    result = await session.exec(
        select(Rating).where(Rating.user_id == user_id, Rating.movie_id == movie_id)
    )
    return result.one_or_none()


async def list_user_ratings(
    session: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Rating]:
    """List all ratings given by a specific user."""
    result = await session.exec(
        select(Rating)
        .where(Rating.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.all()


async def create_rating(
    session: AsyncSession,
    user_id: int,
    rating_data: RatingCreate
) -> Rating:
    """Create a new rating for a movie."""
    rating = Rating(
        user_id=user_id,
        movie_id=rating_data.movie_id,
        rating=rating_data.rating
    )
    session.add(rating)
    await session.commit()
    await session.refresh(rating)
    return rating


async def update_rating(
    session: AsyncSession,
    rating_id: int,
    rating_data: RatingUpdate
) -> Rating | None:
    """Update an existing rating."""
    rating = await get_rating_by_id(session, rating_id)
    if not rating:
        return None
    rating.rating = rating_data.rating
    session.add(rating)
    await session.commit()
    await session.refresh(rating)
    return rating


async def delete_rating(session: AsyncSession, rating_id: int) -> bool:
    """Delete a rating."""
    rating = await get_rating_by_id(session, rating_id)
    if not rating:
        return False
    await session.delete(rating)
    await session.commit()
    return True
