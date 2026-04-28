"""Cinematch FastAPI application entry point."""
from fastapi import FastAPI

app = FastAPI(title="CineMatch", version="1.0.0")

@app.get("/")
async def root():
    """Return a welcome message."""
    return {"message": "CineMatch API"}
