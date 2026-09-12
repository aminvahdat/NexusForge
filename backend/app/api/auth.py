"""Authentication API endpoints for NexusForge."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db_session
from app.auth import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token, get_current_user,
)
from app.models import User

import bcrypt


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(hashed: str, password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegister(BaseModel):
    email: str
    password: str
    username: Optional[str] = None


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db_session: AsyncSession = Depends(get_db_session)):
    result = await db_session.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    new_user = User(
        email=user_data.email,
        username=user_data.username or user_data.email.split('@')[0],
        password_hash=hash_password(user_data.password),
        is_active=True,
    )
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)
    access_token = create_access_token(
        data={"sub": new_user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db_session: AsyncSession = Depends(get_db_session)):
    result = await db_session.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(user.password_hash, user_data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=dict)
async def read_current_user(current_user: User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "is_active": current_user.is_active,
            "is_superuser": current_user.is_superuser,
        }
    }


@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}
