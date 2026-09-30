"""Pytest fixtures: isolated test database and a TestClient with get_db override."""
import os

# Set test environment BEFORE importing the app so the engine binds to the test DB.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_pocketsmart.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("CONTINGENCY_PERCENT", "10")
os.environ.setdefault("GEMINI_API_KEY", "")  # force demo mode

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine, get_db
from app.main import app


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    """A client with a registered + logged-in user (cookie set)."""
    client.post(
        "/api/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"},
    )
    client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "password123"},
    )
    return client
