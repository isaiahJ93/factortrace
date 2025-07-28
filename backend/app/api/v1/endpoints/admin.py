from fastapi import APIRouter, Depends
from app.core.auth import get_current_user

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(current_user = Depends(get_current_user)):
    """Get admin statistics"""
    return {
        "total_users": 0,
        "total_emissions": 0,
        "total_organizations": 0
    }
