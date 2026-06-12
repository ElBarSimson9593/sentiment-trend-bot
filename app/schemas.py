from datetime import datetime

from pydantic import BaseModel, Field


class MentionCreate(BaseModel):
    brand: str = Field(..., min_length=1, max_length=120)
    text: str = Field(..., min_length=1, max_length=5000)
    source: str = Field(default="manual", max_length=80)


class MentionOut(BaseModel):
    id: int
    brand: str
    text: str
    source: str
    sentiment_score: float
    label: str
    created_at: datetime
    alert_triggered: bool = False

    model_config = {"from_attributes": True}


class DashboardMetrics(BaseModel):
    brand: str
    hours: int
    total_mentions: int
    positive: int
    neutral: int
    negative: int
    avg_sentiment: float
    trend: str
    recent_alerts: int


class TimelinePoint(BaseModel):
    bucket: str
    avg_score: float | None = None
    count: int = 0


class TimelineOut(BaseModel):
    brand: str
    hours: int
    points: list[TimelinePoint]


class AlertOut(BaseModel):
    id: int
    brand: str
    negative_count: int
    avg_score: float
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}
