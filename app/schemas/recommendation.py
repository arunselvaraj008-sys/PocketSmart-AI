"""Structured recommendation/plan schemas shared by services and routers."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RecommendationItem(BaseModel):
    name: str
    category: str
    price: float
    platform: str
    reason: str
    url: str


class CategoryAllocation(BaseModel):
    category: str
    items: list[RecommendationItem]
    subtotal: float


class PlanResult(BaseModel):
    planner_type: str
    title: str
    budget: float
    currency: str
    contingency_percent: float
    contingency_amount: float
    allocated: float
    remaining: float
    warnings: list[str] = Field(default_factory=list)
    categories: list[CategoryAllocation]
    source: str = "demo"  # demo | gemini
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class HistoryCreate(BaseModel):
    planner_type: str
    title: str
    budget: float
    payload: dict


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    planner_type: str
    title: str
    budget: float
    created_at: datetime
    payload: dict
