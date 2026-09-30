"""Planner request schemas with strict validation."""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class HomePlannerRequest(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget (positive currency value)")
    rooms: list[str] = Field(..., min_length=1, max_length=10)
    style: str = Field(..., min_length=2, max_length=50)
    quantities: dict[str, int] = Field(default_factory=dict)
    currency: str = "INR"

    @field_validator("quantities")
    @classmethod
    def quantities_non_negative(cls, v: dict[str, int]) -> dict[str, int]:
        for key, value in v.items():
            if value < 0:
                raise ValueError(f"Quantity for '{key}' must be >= 0")
        return v


class PartyPlannerRequest(BaseModel):
    budget: float = Field(..., gt=0)
    guest_count: int = Field(..., gt=0, le=10_000)
    event_type: str = Field(..., min_length=2, max_length=50)
    venue_preference: str = Field(..., min_length=2, max_length=50)
    location: str = Field(..., min_length=2, max_length=100)
    currency: str = "INR"


class JewelryPlannerRequest(BaseModel):
    budget: float = Field(..., gt=0)
    occasion: str = Field(..., min_length=2, max_length=50)
    jewelry_type: str = Field(..., min_length=2, max_length=50)
    style_preference: str = Field(..., min_length=2, max_length=50)
    currency: str = "INR"
    has_outfit_image: bool = False
