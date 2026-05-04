"""Collaborative filtering recommendation logic."""

import math
from typing import List, Dict, Tuple
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func
from app.features.ratings.models import Rating
from app.features.movies.models import Movie


async def get_user_ratings(session: AsyncSession, user_id: int) -> Dict[int, float]:
    """Return {movie_id: rating} for a given user."""
    result = await session.exec(select(Rating).where(Rating.user_id == user_id))
    ratings = result.all()
    return {r.movie_id: float(r.rating) for r in ratings}


async def get_all_users_ratings(session: AsyncSession) -> Dict[int, Dict[int, float]]:
    """Return {user_id: {movie_id: rating}} for all users."""
    result = await session.exec(select(Rating))
    all_ratings = result.all()
    users_ratings: Dict[int, Dict[int, float]] = {}
    for r in all_ratings:
        users_ratings.setdefault(r.user_id, {})[r.movie_id] = float(r.rating)
    return users_ratings


def pearson_correlation(
    ratings1: Dict[int, float], ratings2: Dict[int, float]
) -> float:
    """Pearson correlation between two users' rating vectors."""
    common = set(ratings1.keys()) & set(ratings2.keys())
    if len(common) < 2:
        return 0.0

    r1 = [ratings1[m] for m in common]
    r2 = [ratings2[m] for m in common]

    mean1 = sum(r1) / len(r1)
    mean2 = sum(r2) / len(r2)

    num = sum((r1[i] - mean1) * (r2[i] - mean2) for i in range(len(common)))
    den1 = math.sqrt(sum((r1[i] - mean1) ** 2 for i in range(len(common))))
    den2 = math.sqrt(sum((r2[i] - mean2) ** 2 for i in range(len(common))))

    return 0.0 if den1 == 0 or den2 == 0 else num / (den1 * den2)


async def get_most_popular_movies(session: AsyncSession, limit: int = 10) -> List[Tuple[Movie, float]]:
    """Return top-rated movies by average rating (used for cold start).

    Returns list of (movie, avg_rating) tuples.
    """
    stmt = (
        select(Movie, func.avg(Rating.rating).label("avg_rating"))
        .join(Rating, Movie.id == Rating.movie_id)
        .group_by(Movie.id)
        .order_by(func.avg(Rating.rating).desc())
        .limit(limit)
    )
    result = await session.exec(stmt)
    movies_with_avg = result.all()
    return [(movie, round(avg, 2)) for movie, avg in movies_with_avg]


def _get_similar_users_from_ratings(
    user_id: int,
    user_ratings: Dict[int, float],
    all_ratings: Dict[int, Dict[int, float]],
    similarity_threshold: float,
    k_neighbors: int
) -> List[Tuple[int, float]]:
    """Return list of (user_id, similarity) for top neighbors (synchronous, no DB calls)."""
    other_users = {uid: r for uid, r in all_ratings.items() if uid != user_id}

    sims = []
    for oid, oratings in other_users.items():
        sim = pearson_correlation(user_ratings, oratings)
        if sim > similarity_threshold:
            sims.append((oid, sim))

    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:k_neighbors]


async def _compute_predictions(
    user_ratings: Dict[int, float],
    all_ratings: Dict[int, Dict[int, float]],
    similar_users: List[Tuple[int, float]]
) -> Dict[int, float]:
    """Return {movie_id: predicted_rating} for movies not rated by user."""
    neighbor_data: Dict[int, List[Tuple[float, float]]] = {}
    for neighbor_id, sim in similar_users:
        nb_ratings = all_ratings[neighbor_id]
        for movie_id, rating in nb_ratings.items():
            if movie_id not in user_ratings:
                neighbor_data.setdefault(movie_id, []).append((rating, sim))

    predictions = {}
    for movie_id, val in neighbor_data.items():
        num = sum(r * s for r, s in val)
        den = sum(s for _, s in val)
        if den > 0:
            predictions[movie_id] = round(num / den, 2)

    return predictions



async def get_top_n_recommendations(
    session: AsyncSession,
    user_id: int,
    n: int = 10,
    similarity_threshold: float = 0.0,
    k_neighbors: int = 5
) -> List[Tuple[Movie, float, str]]:
    """Return list of (movie, predicted_rating, reason) for top N recommendations.

    reason is either "popular" (cold start / fallback) or "collaborative" (CF).
    """
    user_ratings = await get_user_ratings(session, user_id)
    if len(user_ratings) < 3:
        popular = await get_most_popular_movies(session, n)
        return [(m, r, "popular") for m, r in popular]

    all_ratings = await get_all_users_ratings(session)
    similar_users = _get_similar_users_from_ratings(
        user_id, user_ratings, all_ratings, similarity_threshold, k_neighbors
    )
    if not similar_users:
        popular = await get_most_popular_movies(session, n)
        return [(m, r, "popular") for m, r in popular]

    predictions = await _compute_predictions(user_ratings, all_ratings, similar_users)
    if not predictions:
        popular = await get_most_popular_movies(session, n)
        return [(m, r, "popular") for m, r in popular]

    sorted_pred = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:n]
    result = []
    for movie_id, pred_rating in sorted_pred:
        movie = (await session.exec(select(Movie).where(Movie.id == movie_id))).one_or_none()
        if movie:
            result.append((movie, pred_rating, "collaborative"))
    return result
