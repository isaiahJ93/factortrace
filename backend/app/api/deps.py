from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User

# Security scheme
security = HTTPBearer(auto_error=False)

async def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user from token (simplified version)
    For now, returns a mock user or None
    """
    # TODO: Implement actual JWT token validation
    
    # For development, return a mock user
    # In production, you would validate the JWT token and get the user from DB
    if not credentials:
        # Return None for optional auth endpoints
        return None
    
    # Mock user for development
    mock_user = User(
        id=1,
        email="test@example.com",
        organization_id=1,
        is_active=True
    )
    
    return mock_user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require an authenticated user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user
