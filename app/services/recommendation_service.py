"""Recommendation orchestration: deterministic mock engine + optional Gemini.

The mock engine always produces a valid, budget-aware plan. When Gemini is
available we ask it for a strict-JSON plan built only from the mock catalog;
if the response validates (known items, prices, within budget) we use it and
mark the plan source as "gemini", otherwise we fall back to the mock plan.
"""
import json
from typing import Optional

from app.core.config import settings
from app.schemas.planners import HomePlannerRequest, JewelryPlannerRequest, PartyPlannerRequest
from app.schemas.recommendation import CategoryAllocation, PlanResult, RecommendationItem
from app.services import gemini_service, mock_catalog_service
from app.services.provider_service import build_link


# ---------------------------------------------------------------------------
# Prompt templates — emphasise budget adherence, allocation, practical picks,
# and forbid invented live prices.
# ---------------------------------------------------------------------------

def _catalog_summary(catalog: dict) -> str:
    return json.dumps(
        {cat: [{"name": i["name"], "price": i["price"], "platform": i["platform"]} for i in items]
         for cat, items in catalog.items()},
        indent=2,
    )


def build_home_prompt(request: HomePlannerRequest) -> str:
    return f"""You are a home interior budget planner. Create a budget-aware plan using ONLY the items in the catalog below — do not invent products or live prices.

Budget: {request.budget} {request.currency}
Rooms: {', '.join(request.rooms)}
Style: {request.style}
Quantities requested: {json.dumps(request.quantities)}
Contingency reserve: {settings.CONTINGENCY_PERCENT}% of the budget must be held back.

Catalog:
{_catalog_summary(mock_catalog_service.HOME_CATALOG)}

Return STRICT JSON with exactly this structure and no other text:
{{"categories": [{{"category": "...", "items": [{{"name": "...", "price": 0, "platform": "...", "reason": "..."}}], "subtotal": 0}}]}}

Rules:
- Use only items from the catalog; price and platform must match the catalog exactly.
- The sum of all subtotals must stay within the budget after the contingency reserve.
- Give a practical, specific reason for each item.
- Cover the requested quantities where possible."""


def build_party_prompt(request: PartyPlannerRequest) -> str:
    return f"""You are a party budget planner. Create a budget-aware plan using ONLY the items in the catalog below — do not invent services or live prices.

Budget: {request.budget} {request.currency}
Guests: {request.guest_count}
Event type: {request.event_type}
Venue preference: {request.venue_preference}
Location: {request.location}
Contingency reserve: {settings.CONTINGENCY_PERCENT}% of the budget must be held back.

Catalog:
{_catalog_summary(mock_catalog_service.PARTY_CATALOG)}

Return STRICT JSON with exactly this structure and no other text:
{{"categories": [{{"category": "...", "items": [{{"name": "...", "price": 0, "platform": "...", "reason": "..."}}], "subtotal": 0}}]}}

Rules:
- Use only items from the catalog; price and platform must match the catalog exactly.
- For per-person items (catering, gifts), multiply the catalog price by the guest count.
- The sum of all subtotals must stay within the budget after the contingency reserve.
- Cover catering, decorations, entertainment and venue at minimum."""


def build_jewelry_prompt(request: JewelryPlannerRequest) -> str:
    return f"""You are a jewelry budget planner. Create a budget-aware plan using ONLY the items in the catalog below — do not invent products or live prices.

Budget: {request.budget} {request.currency}
Occasion: {request.occasion}
Jewelry type: {request.jewelry_type}
Style preference: {request.style_preference}
Contingency reserve: {settings.CONTINGENCY_PERCENT}% of the budget must be held back.

Catalog:
{_catalog_summary(mock_catalog_service.JEWELRY_CATALOG)}

Return STRICT JSON with exactly this structure and no other text:
{{"categories": [{{"category": "...", "items": [{{"name": "...", "price": 0, "platform": "...", "reason": "..."}}], "subtotal": 0}}]}}

Rules:
- Use only items from the catalog; price and platform must match the catalog exactly.
- The sum of all subtotals must stay within the budget after the contingency reserve.
- Recommend coordinated pieces that suit the occasion and style."""


# ---------------------------------------------------------------------------
# Gemini response validation — only accept plans built from the mock catalog.
# ---------------------------------------------------------------------------

def _validate_gemini_plan(data: dict, catalog: dict, budget: float) -> Optional[list[CategoryAllocation]]:
    """Return validated CategoryAllocation list, or None if the plan is invalid."""
    cats = data.get("categories")
    if not isinstance(cats, list) or not cats:
        return None

    # Build a lookup of catalog items by name.
    lookup = {
        i["name"]: i
        for items in catalog.values()
        for i in items
    }

    result: list[CategoryAllocation] = []
    total = 0.0
    for cat in cats:
        if not isinstance(cat, dict):
            return None
        cat_name = cat.get("category")
        items = cat.get("items")
        if not isinstance(cat_name, str) or not isinstance(items, list) or not items:
            return None
        cat_items: list[RecommendationItem] = []
        subtotal = 0.0
        for it in items:
            if not isinstance(it, dict):
                return None
            name = it.get("name")
            if name not in lookup:
                return None  # invented item — reject
            ref = lookup[name]
            price = it.get("price")
            if not isinstance(price, (int, float)) or float(price) != float(ref["price"]):
                return None  # price mismatch — reject
            cat_items.append(
                RecommendationItem(
                    name=name,
                    category=cat_name,
                    price=float(price),
                    platform=ref["platform"],
                    reason=str(it.get("reason", "Recommended to fit your budget and style.")),
                    url=build_link(ref["platform"], name),
                )
            )
            subtotal += float(price)
        subtotal = round(subtotal, 2)
        total += subtotal
        result.append(CategoryAllocation(category=cat_name, items=cat_items, subtotal=subtotal))

    contingency = round(budget * settings.CONTINGENCY_PERCENT / 100, 2)
    if total > budget - contingency:
        return None  # over budget — reject
    return result


def _gemini_plan(
    prompt: str, catalog: dict, budget: float, planner_type: str, title: str, currency: str,
    notes: Optional[str] = None,
) -> Optional[PlanResult]:
    data = gemini_service.generate_plan_json(prompt)
    if not data:
        return None
    categories = _validate_gemini_plan(data, catalog, budget)
    if not categories:
        return None
    contingency = round(budget * settings.CONTINGENCY_PERCENT / 100, 2)
    allocated = round(sum(c.subtotal for c in categories), 2)
    remaining = round(budget - allocated - contingency, 2)
    warnings = []
    if remaining < 0:
        warnings.append("Plan exceeds budget after the contingency reserve.")
    return PlanResult(
        planner_type=planner_type,
        title=title,
        budget=budget,
        currency=currency,
        contingency_percent=settings.CONTINGENCY_PERCENT,
        contingency_amount=contingency,
        allocated=allocated,
        remaining=remaining,
        warnings=warnings,
        categories=categories,
        source="gemini",
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_home_plan(request: HomePlannerRequest) -> PlanResult:
    mock = mock_catalog_service.build_home_plan(
        request.budget, request.rooms, request.style, request.quantities, request.currency
    )
    if gemini_service.is_available():
        title = f"{request.style.title()} home plan for {len(request.rooms)} room{'s' if len(request.rooms) > 1 else ''}"
        plan = _gemini_plan(
            build_home_prompt(request), mock_catalog_service.HOME_CATALOG,
            request.budget, "home", title, request.currency,
        )
        if plan:
            return plan
    return mock


def build_party_plan(request: PartyPlannerRequest) -> PlanResult:
    mock = mock_catalog_service.build_party_plan(
        request.budget, request.guest_count, request.event_type,
        request.venue_preference, request.location, request.currency,
    )
    if gemini_service.is_available():
        title = f"{request.event_type.title()} for {request.guest_count} guests in {request.location}"
        plan = _gemini_plan(
            build_party_prompt(request), mock_catalog_service.PARTY_CATALOG,
            request.budget, "party", title, request.currency,
        )
        if plan:
            return plan
    return mock


def build_jewelry_plan(
    request: JewelryPlannerRequest, outfit_analysis: Optional[str] = None
) -> PlanResult:
    mock = mock_catalog_service.build_jewelry_plan(
        request.budget, request.occasion, request.jewelry_type,
        request.style_preference, request.currency, outfit_analysis,
    )
    if gemini_service.is_available():
        title = f"{request.occasion.title()} {request.jewelry_type.lower()} in {request.style_preference.lower()} style"
        plan = _gemini_plan(
            build_jewelry_prompt(request), mock_catalog_service.JEWELRY_CATALOG,
            request.budget, "jewelry", title, request.currency, notes=outfit_analysis,
        )
        if plan:
            return plan
    return mock
