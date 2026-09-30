"""PocketSmart AI application factory and entry point."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth, history, pages, planners


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME, version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure upload directory exists.
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    Base.metadata.create_all(bind=engine)

    app.include_router(auth.router)
    app.include_router(pages.router)
    app.include_router(planners.router)
    app.include_router(history.router)

    return app


app = create_app()
