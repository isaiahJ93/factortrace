from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def list_items(db: Session = Depends(get_db)):
    """List items"""
    return {"items": [], "total": 0}

@router.post("/")
async def create_item(db: Session = Depends(get_db)):
    """Create item"""
    return {"message": "Not implemented"}
