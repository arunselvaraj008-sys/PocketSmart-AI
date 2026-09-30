"""Authentication tests: register, login, logout, protected routes, validation."""


def test_register_success(client):
    res = client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "password123"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    payload = {"username": "bob", "email": "bob@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    res = client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob2@example.com", "password": "password123"},
    )
    assert res.status_code == 409


def test_register_duplicate_email(client):
    payload = {"username": "carol", "email": "carol@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    res = client.post(
        "/api/auth/register",
        json={"username": "carol2", "email": "carol@example.com", "password": "password123"},
    )
    assert res.status_code == 409


def test_register_validation(client):
    # short username
    res = client.post(
        "/api/auth/register",
        json={"username": "ab", "email": "a@b.com", "password": "password123"},
    )
    assert res.status_code == 422
    # short password
    res = client.post(
        "/api/auth/register",
        json={"username": "validuser", "email": "a@b.com", "password": "short"},
    )
    assert res.status_code == 422
    # invalid email
    res = client.post(
        "/api/auth/register",
        json={"username": "validuser", "email": "not-an-email", "password": "password123"},
    )
    assert res.status_code == 422


def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"username": "dave", "email": "dave@example.com", "password": "password123"},
    )
    res = client.post(
        "/api/auth/login",
        json={"username": "dave", "password": "password123"},
    )
    assert res.status_code == 200
    assert res.json()["token_type"] == "bearer"
    assert res.json()["access_token"]


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"username": "erin", "email": "erin@example.com", "password": "password123"},
    )
    res = client.post(
        "/api/auth/login",
        json={"username": "erin", "password": "wrongpassword"},
    )
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "password123"},
    )
    assert res.status_code == 401


def test_protected_route_requires_auth(client):
    res = client.get("/api/history")
    assert res.status_code == 401


def test_me_with_auth(auth_client):
    res = auth_client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"


def test_logout(auth_client):
    res = auth_client.post("/api/auth/logout")
    assert res.status_code == 200
    # Cookie cleared; subsequent protected call should 401.
    res = auth_client.get("/api/auth/me")
    assert res.status_code == 401


def test_pages_protected(client):
    assert client.get("/dashboard", follow_redirects=False).status_code == 302
    assert client.get("/planners/home", follow_redirects=False).status_code == 302
    assert client.get("/history", follow_redirects=False).status_code == 302


def test_pages_accessible_when_authed(auth_client):
    assert auth_client.get("/dashboard").status_code == 200
    assert auth_client.get("/planners/home").status_code == 200
    assert auth_client.get("/history").status_code == 200
