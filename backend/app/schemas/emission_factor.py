from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmissionFactorBase(BaseModel):
    name: str
    category: str
    scope: int
    factor: float
    unit: str
    source: Optional[str] = None
    description: Optional[str] = None

class EmissionFactorCreate(EmissionFactorBase):
    pass

class EmissionFactorUpdate(BaseModel):
    name: Optional[str] = None
    factor: Optional[float] = None
    is_active: Optional[bool] = None

class EmissionFactor(EmissionFactorBase):
    id: int
    is_active: bool
    valid_from: datetime
    valid_to: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
