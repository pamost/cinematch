"""Cinematch FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import init_db
from app.features.auth.router import router as auth_router
from app.features.movies.router import router as movies_router
from app.features.ratings.router import router as ratings_router
from app.features.recommendations.router import router as recommendations_router


@asynccontextmanager
async def lifespan(_app: FastAPI):  # переименовали, чтобы избежать конфликта
    """Handle startup and shutdown events."""
    await init_db()
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
