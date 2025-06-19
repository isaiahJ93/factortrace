from pydantic import BaseModel

class EmissionRecord(BaseModel):
    source: str
    amount: float
    unit: str