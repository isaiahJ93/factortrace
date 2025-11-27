"""Authentication endpoints"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """User login"""
    # For testing, accept any credentials
    token_data = {
        "sub": request.email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    access_token = jwt.encode(token_data, settings.jwt_secret, algorithm="HS256")
    return LoginResponse(access_token=access_token)

@router.get("/verify")
async def verify_token():
    """Verify API is working"""
    return {"status": "auth endpoint working"}
