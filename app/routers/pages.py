"""Jinja2 page routes. Protected pages redirect unauthenticated users to /login."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.templating import templates
from app.models.recommendation import RecommendationHistory
from app.models.user import User

router = APIRouter()


def _get_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    return db.query(User).filter(User.id == payload.get("sub")).first()


def _require_user(request: Request, db: Session) -> User:
    user = _get_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return user


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "index.html", {"user": _get_user(request, db)})


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if _get_user(request, db):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "login.html", {"user": None})


@router.get("/register")
def register_page(request: Request, db: Session = Depends(get_db)):
    if _get_user(request, db):
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(request, "register.html", {"user": None})


@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    recent = (
        db.query(RecommendationHistory)
        .filter(RecommendationHistory.user_id == user.id)
        .order_by(RecommendationHistory.created_at.desc())
        .limit(6)
        .all()
    )
    return templates.TemplateResponse(request, "dashboard.html", {"user": user, "recent": recent})


@router.get("/planners/home")
def home_planner(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "home_planner.html", {"user": user})


@router.get("/planners/party")
def party_planner(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "party_planner.html", {"user": user})


@router.get("/planners/jewelry")
def jewelry_planner(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    return templates.TemplateResponse(request, "jewelry_planner.html", {"user": user})


@router.get("/results/{plan_id}")
def results(request: Request, plan_id: int, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
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
    return templates.TemplateResponse(request, "results.html", {"user": user, "plan": item})


@router.get("/history")
def history(request: Request, db: Session = Depends(get_db)):
    user = _require_user(request, db)
    if isinstance(user, RedirectResponse):
        return user
    items = (
        db.query(RecommendationHistory)
        .filter(RecommendationHistory.user_id == user.id)
        .order_by(RecommendationHistory.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(request, "history.html", {"user": user, "items": items})


@router.get("/testimonials")
def testimonials(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "testimonials.html", {"user": _get_user(request, db)})
