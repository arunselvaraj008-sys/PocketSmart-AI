"""History tests: save, list, view, delete, and per-user access isolation."""


def _make_home_plan(client, budget=40000):
    res = client.post(
        "/api/planners/home",
        json={"budget": budget, "rooms": ["living room"], "style": "Modern", "quantities": {}},
    )
    assert res.status_code == 200
    return res.json()["id"]


def test_plan_saved_to_history(auth_client):
    plan_id = _make_home_plan(auth_client)
    res = auth_client.get("/api/history")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["id"] == plan_id
    assert items[0]["planner_type"] == "home"
    assert items[0]["budget"] == 40000


def test_history_empty_for_new_user(client):
    client.post("/api/auth/register",
                json={"username": "solo", "email": "solo@example.com", "password": "password123"})
    client.post("/api/auth/login",
                json={"username": "solo", "password": "password123"})
    res = client.get("/api/history")
    assert res.status_code == 200
    assert res.json() == []


def test_view_single_plan(auth_client):
    plan_id = _make_home_plan(auth_client)
    res = auth_client.get(f"/api/history/{plan_id}")
    assert res.status_code == 200
    assert res.json()["id"] == plan_id


def test_delete_plan(auth_client):
    plan_id = _make_home_plan(auth_client)
    res = auth_client.delete(f"/api/history/{plan_id}")
    assert res.status_code == 200
    # Now gone.
    assert auth_client.get(f"/api/history/{plan_id}").status_code == 404
    assert auth_client.get("/api/history").json() == []


def test_delete_missing_plan(auth_client):
    res = auth_client.delete("/api/history/9999")
    assert res.status_code == 404


def test_access_isolation_between_users(auth_client):
    # User A creates a plan.
    plan_id = _make_home_plan(auth_client)

    # User B registers and must not see User A's plan.
    auth_client.post("/api/auth/register",
                     json={"username": "mallory", "email": "mallory@example.com",
                           "password": "password123"})
    auth_client.post("/api/auth/login",
                     json={"username": "mallory", "password": "password123"})

    assert auth_client.get("/api/history").json() == []
    assert auth_client.get(f"/api/history/{plan_id}").status_code == 404
    assert auth_client.delete(f"/api/history/{plan_id}").status_code == 404


def test_history_requires_auth(client):
    assert client.get("/api/history").status_code == 401
    assert client.get("/api/history/1").status_code == 401
    assert client.delete("/api/history/1").status_code == 401


def test_multiple_plans_listed(auth_client):
    _make_home_plan(auth_client, budget=30000)
    _make_home_plan(auth_client, budget=60000)
    res = auth_client.get("/api/history")
    assert len(res.json()) == 2
