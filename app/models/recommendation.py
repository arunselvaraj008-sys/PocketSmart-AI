"""Recommendation history model — stores every generated plan per user."""
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    planner_type = Column(String(30), nullable=False)  # home | party | jewelry
    title = Column(String(200), nullable=False)
    budget = Column(Float, nullable=False)
    payload = Column(JSON, nullable=False)  # full PlanResult as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")
