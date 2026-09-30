"""Planner tests: validation, mock fallback, budget totals, image upload."""
from app.services import gemini_service, recommendation_service
from app.schemas.planners import HomePlannerRequest, JewelryPlannerRequest, PartyPlannerRequest


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_home_budget_must_be_positive(auth_client):
    res = auth_client.post(
        "/api/planners/home",
        json={"budget": 0, "rooms": ["living room"], "style": "Modern", "quantities": {}},
    )
    assert res.status_code == 422


def test_home_negative_quantity_rejected(auth_client):
    res = auth_client.post(
        "/api/planners/home",
        json={"budget": 10000, "rooms": ["living room"], "style": "Modern",
              "quantities": {"lights": -1}},
    )
    assert res.status_code == 422


def test_home_rooms_required(auth_client):
    res = auth_client.post(
        "/api/planners/home",
        json={"budget": 10000, "rooms": [], "style": "Modern", "quantities": {}},
    )
    assert res.status_code == 422


def test_party_guest_count_validation(auth_client):
    res = auth_client.post(
        "/api/planners/party",
        json={"budget": 10000, "guest_count": 0, "event_type": "Birthday",
              "venue_preference": "Home", "location": "Mumbai"},
    )
    assert res.status_code == 422


def test_party_budget_validation(auth_client):
    res = auth_client.post(
        "/api/planners/party",
        json={"budget": -500, "guest_count": 10, "event_type": "Birthday",
              "venue_preference": "Home", "location": "Mumbai"},
    )
    assert res.status_code == 422


def test_jewelry_budget_validation(auth_client):
    res = auth_client.post(
        "/api/planners/jewelry",
        data={"budget": "0", "occasion": "Wedding", "jewelry_type": "Earrings",
              "style_preference": "Traditional"},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Mock fallback (demo mode — no API key configured in tests)
# ---------------------------------------------------------------------------

def test_gemini_unavailable_in_tests():
    assert gemini_service.is_available() is False


def test_home_plan_mock_fallback(auth_client):
    res = auth_client.post(
        "/api/planners/home",
        json={"budget": 50000, "rooms": ["living room", "bedroom"], "style": "Modern",
              "quantities": {"lights": 2, "fans": 2, "sofas": 1, "decor": 3}},
    )
    assert res.status_code == 200
    body = res.json()
    assert "id" in body
    assert body["redirect"].startswith("/results/")

    plan = auth_client.get(f"/api/history/{body['id']}").json()["payload"]
    assert plan["source"] == "demo"
    assert plan["allocated"] + plan["contingency_amount"] <= plan["budget"] + 0.01
    assert plan["remaining"] >= 0
    assert len(plan["categories"]) > 0
    for cat in plan["categories"]:
        assert cat["subtotal"] == round(sum(i["price"] for i in cat["items"]), 2)
        for item in cat["items"]:
            assert item["name"] and item["platform"] and item["reason"] and item["url"]


def test_party_plan_mock_fallback(auth_client):
    res = auth_client.post(
        "/api/planners/party",
        json={"budget": 30000, "guest_count": 50, "event_type": "Birthday",
              "venue_preference": "Home", "location": "Mumbai"},
    )
    assert res.status_code == 200
    plan_id = res.json()["id"]
    plan = auth_client.get(f"/api/history/{plan_id}").json()["payload"]
    assert plan["source"] == "demo"
    assert plan["allocated"] + plan["contingency_amount"] <= plan["budget"] + 0.01
    cats = {c["category"] for c in plan["categories"]}
    assert "Catering" in cats


def test_jewelry_plan_mock_fallback(auth_client):
    res = auth_client.post(
        "/api/planners/jewelry",
        data={"budget": "15000", "occasion": "Wedding", "jewelry_type": "Earrings",
              "style_preference": "Traditional"},
    )
    assert res.status_code == 200
    plan_id = res.json()["id"]
    plan = auth_client.get(f"/api/history/{plan_id}").json()["payload"]
    assert plan["source"] == "demo"
    assert plan["allocated"] + plan["contingency_amount"] <= plan["budget"] + 0.01


# ---------------------------------------------------------------------------
# Budget totals (service-level invariants)
# ---------------------------------------------------------------------------

def test_home_plan_budget_invariants():
    req = HomePlannerRequest(budget=80000, rooms=["living room", "bedroom", "kitchen"],
                             style="Scandinavian",
                             quantities={"lights": 3, "fans": 3, "tables": 1, "sofas": 1, "decor": 4})
    plan = recommendation_service.build_home_plan(req)
    assert plan.source == "demo"
    assert plan.contingency_amount == round(80000 * 0.10, 2)
    assert plan.allocated + plan.contingency_amount <= plan.budget + 0.01
    assert plan.remaining >= 0
    assert plan.remaining == round(plan.budget - plan.allocated - plan.contingency_amount, 2)


def test_party_plan_budget_invariants():
    req = PartyPlannerRequest(budget=50000, guest_count=80, event_type="Birthday",
                              venue_preference="Banquet Hall", location="Delhi")
    plan = recommendation_service.build_party_plan(req)
    assert plan.allocated + plan.contingency_amount <= plan.budget + 0.01
    assert plan.remaining >= 0


def test_jewelry_plan_budget_invariants():
    req = JewelryPlannerRequest(budget=20000, occasion="Wedding", jewelry_type="Bridal Set",
                                style_preference="Traditional")
    plan = recommendation_service.build_jewelry_plan(req)
    assert plan.allocated + plan.contingency_amount <= plan.budget + 0.01
    assert plan.remaining >= 0


def test_tight_budget_stays_within_bounds():
    req = HomePlannerRequest(budget=5000, rooms=["bedroom"], style="Minimalist", quantities={})
    plan = recommendation_service.build_home_plan(req)
    assert plan.allocated + plan.contingency_amount <= plan.budget + 0.01


# ---------------------------------------------------------------------------
# Image upload validation
# ---------------------------------------------------------------------------

def test_jewelry_rejects_non_image(auth_client):
    res = auth_client.post(
        "/api/planners/jewelry",
        data={"budget": "10000", "occasion": "Party", "jewelry_type": "Earrings",
              "style_preference": "Modern"},
        files={"outfit_image": ("notes.txt", b"not an image", "text/plain")},
    )
    assert res.status_code == 415


def test_jewelry_rejects_oversized_image(auth_client):
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (6 * 1024 * 1024)  # > 5 MB
    res = auth_client.post(
        "/api/planners/jewelry",
        data={"budget": "10000", "occasion": "Party", "jewelry_type": "Earrings",
              "style_preference": "Modern"},
        files={"outfit_image": ("big.png", big, "image/png")},
    )
    assert res.status_code == 413


def test_jewelry_accepts_valid_image(auth_client):
    # Minimal valid PNG header + a few bytes.
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    res = auth_client.post(
        "/api/planners/jewelry",
        data={"budget": "10000", "occasion": "Party", "jewelry_type": "Earrings",
              "style_preference": "Modern"},
        files={"outfit_image": ("outfit.png", png, "image/png")},
    )
    assert res.status_code == 200
    plan = auth_client.get(f"/api/history/{res.json()['id']}").json()["payload"]
    assert plan["source"] == "demo"
