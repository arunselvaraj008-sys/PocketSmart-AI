"""Planner API endpoints. All routes are protected. Each generated plan is
persisted to the user's history and a redirect URL is returned."""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.recommendation import RecommendationHistory
from app.models.user import User
from app.schemas.planners import HomePlannerRequest, JewelryPlannerRequest, PartyPlannerRequest
from app.services import gemini_service, recommendation_service

router = APIRouter(prefix="/api/planners", tags=["planners"])

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
IMAGE_MAGIC_BYTES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"RIFF": "image/webp",  # WEBP starts with RIFF....WEBP
}


def _validate_image(content: bytes, declared_type: str) -> str:
    """Validate upload type, size, and magic bytes. Returns the safe MIME type."""
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
        )
    detected = None
    for magic, mime in IMAGE_MAGIC_BYTES.items():
        if content.startswith(magic):
            detected = mime
            break
    if detected == "image/webp" and b"WEBP" not in content[:16]:
        detected = None
    if detected is None:
        raise HTTPException(status_code=415, detail="Invalid image content")
    if declared_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Only PNG, JPG and WEBP images are allowed")
    return detected


def _save_plan(db: Session, user: User, planner_type: str, title: str, budget: float, payload: dict) -> RecommendationHistory:
    history = RecommendationHistory(
        user_id=user.id,
        planner_type=planner_type,
        title=title,
        budget=budget,
        payload=payload,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


@router.post("/home")
def home(
    request: HomePlannerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = recommendation_service.build_home_plan(request)
    history = _save_plan(db, user, "home", plan.title, request.budget, plan.model_dump())
    return {"id": history.id, "redirect": f"/results/{history.id}"}


@router.post("/party")
def party(
    request: PartyPlannerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    plan = recommendation_service.build_party_plan(request)
    history = _save_plan(db, user, "party", plan.title, request.budget, plan.model_dump())
    return {"id": history.id, "redirect": f"/results/{history.id}"}


@router.post("/jewelry")
async def jewelry(
    budget: float = Form(..., gt=0),
    occasion: str = Form(..., min_length=2, max_length=50),
    jewelry_type: str = Form(..., min_length=2, max_length=50),
    style_preference: str = Form(..., min_length=2, max_length=50),
    currency: str = Form("INR"),
    outfit_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    outfit_analysis: Optional[str] = None
    has_image = False

    if outfit_image and outfit_image.filename:
        content = await outfit_image.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded image is empty")
        mime = _validate_image(content, outfit_image.content_type or "")
        has_image = True
        prompt = (
            "You are a jewelry stylist. Analyze the outfit in this image and suggest "
            "coordinated jewelry styles, metals and colors that would complement it. "
            "Keep the response under 120 words and focus on practical, purchasable advice."
        )
        outfit_analysis = gemini_service.analyze_outfit_image(content, mime, prompt)

    request = JewelryPlannerRequest(
        budget=budget,
        occasion=occasion,
        jewelry_type=jewelry_type,
        style_preference=style_preference,
        currency=currency,
        has_outfit_image=has_image,
    )
    plan = recommendation_service.build_jewelry_plan(request, outfit_analysis=outfit_analysis)
    history = _save_plan(db, user, "jewelry", plan.title, request.budget, plan.model_dump())
    return {"id": history.id, "redirect": f"/results/{history.id}"}
