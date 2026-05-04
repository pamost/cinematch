"""API routes for recommendations feature."""

from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.auth import get_current_user
from app.features.auth.models import User
from app.features.recommendations import service as rec_service
from app.features.recommendations.schemas import RecommendedMovie

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=list[RecommendedMovie])
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get movie recommendations for current user."""
    # Вызываем сервис, который возвращает список (Movie, predicted_rating, reason)
    movies_with_ratings = await rec_service.get_top_n_recommendations(
        session, current_user.id, n=limit
    )
    # Преобразуем в список RecommendedMovie
    return [
        RecommendedMovie(id=m.id, title=m.title, predicted_rating=r, reason=reason)
        for m, r, reason in movies_with_ratings
    ]
