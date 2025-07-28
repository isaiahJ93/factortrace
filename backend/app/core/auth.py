# backend/app/core/auth.py
"""
Authentication stub for development
Replace this with real authentication later
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Optional: Use bearer token security scheme
security = HTTPBearer(auto_error=False)

class User:
    """Mock user class"""
    def __init__(self, id: int, email: str, name: str = None):
        self.id = id
        self.email = email
        self.name = name

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user from authentication
    For now, returns None (no authentication) or a mock user
    
    To test with authentication, pass a Bearer token in the Authorization header
    """
    # For development: return None to bypass authentication
    return None
    
    # Optional: Return a mock user for testing
    # return User(id=1, email="test@example.com", name="Test User")
    
    # Optional: Check for a simple token
    # if credentials and credentials.credentials == "test-token":
    #     return User(id=1, email="test@example.com", name="Test User")
    # return None