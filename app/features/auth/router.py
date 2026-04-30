"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.auth import create_access_token
from app.features.auth.schemas import UserCreate, Token, UserOut
from app.features.auth.service import create_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    existing = await authenticate_user(session, user_data.username, user_data.password)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = await create_user(session, user_data.username, user_data.password)
    return user

@router.post("/login", response_model=Token)
async def login(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    user = await authenticate_user(session, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
