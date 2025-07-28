from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    