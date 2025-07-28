from pydantic import BaseModel

class EmissionsRecord(BaseModel):
    gas: str
    amount: float
    unit: str
    source: str
    confidence: float
    method_used: str
    activity_description: str
    activity_value: float
    activity_unit: str

    