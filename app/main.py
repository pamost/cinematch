"""Cinematch FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.features.auth.router import router as auth_router
from app.features.movies.router import router as movies_router
from app.features.ratings.router import router as ratings_router
from app.features.recommendations.router import router as recommendations_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Handle startup and shutdown events.

    Внимание: схема БД теперь управляется через Alembic (alembic upgrade head).
    Перед первым запуском примените миграции:
        alembic upgrade head
    """
    yield


app = FastAPI(
    title="CineMatch",
    description="Collaborative filtering movie recommendations",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(ratings_router)
app.include_router(recommendations_router)

@app.get("/")
async def root():
    """Return a welcome message."""
    return {"message": "CineMatch API"}
