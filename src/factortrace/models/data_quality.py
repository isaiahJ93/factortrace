from pydantic import BaseModel
from factortrace.enums import DataQualityTierEnum  # assuming this exists

class DataQualityType(BaseModel):
    tier: DataQualityTierEnum
    source: str
    confidence_score: float

    