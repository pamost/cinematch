"""Pydantic schemas for authentication."""

from pydantic import BaseModel


class UserCreate(BaseModel):
    """Schema for user registration request."""
    username: str
    password: str


class UserOut(BaseModel):
    """Schema for user response (safe, no password)."""
    id: int
    username: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token payload (internal use)."""
    user_id: int
