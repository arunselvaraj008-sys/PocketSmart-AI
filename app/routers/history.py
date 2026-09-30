"""Recommendation history API: list, view, delete. All routes are protected
and strictly isolated per user."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.recommendation import RecommendationHistory
from app.models.user import User

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def list_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = (
        db.query(RecommendationHistory)
        .filter(RecommendationHistory.user_id == user.id)
        .order_by(RecommendationHistory.created_at.desc())
        .all()
    )
    return items


@router.get("/{plan_id}")
def get_history(plan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = (
        db.query(RecommendationHistory)
        .filter(
            RecommendationHistory.id == plan_id,
            RecommendationHistory.user_id == user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Plan not found")
    return item


@router.delete("/{plan_id}")
def delete_history(plan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = (
        db.query(RecommendationHistory)
        .filter(
            RecommendationHistory.id == plan_id,
            RecommendationHistory.user_id == user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(item)
    db.commit()
    return {"message": "Plan deleted"}
