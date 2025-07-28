from __future__ import annotations
from pydantic import BaseModel


class EmissionData(BaseModel):
    source: str
    amount: float
    unit: str
