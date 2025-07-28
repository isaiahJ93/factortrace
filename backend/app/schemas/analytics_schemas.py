"""
Analytics and insights schemas for GHG Protocol Scope 3 Calculator
"""

from datetime import date
from typing import Dict, List, Optional, Union

from pydantic import Field

from app.schemas.base_schemas import BaseResponse


class AnalyticsMetric(BaseResponse):
    """Single analytics metric"""
    name: str
    value: float
    unit: str
    trend: Optional[str] = Field(None, pattern="^(increasing|decreasing|stable)$")
    change_percentage: Optional[float] = None


class AnalyticsResponse(BaseResponse):
    """Analytics and insights response"""
    period_start: date
    period_end: date
    metrics: List[AnalyticsMetric]
    time_series: Optional[Dict[str, List[Dict[str, Union[str, float]]]]] = None
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
