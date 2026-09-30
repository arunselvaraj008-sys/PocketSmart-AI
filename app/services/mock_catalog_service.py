"""Mock catalog data and budget-aware selection for all three planners.

This module is the deterministic recommendation engine. It powers demo mode
(Gemini unavailable) and acts as the fallback when Gemini returns malformed
output. All data is realistic but simulated — no live prices are fetched and
no sites are scraped. Swap in licensed APIs via provider_service when ready.
"""
from typing import Optional

from app.core.config import settings
from app.schemas.recommendation import CategoryAllocation, PlanResult, RecommendationItem
from app.services.provider_service import build_link

# ---------------------------------------------------------------------------
# Catalogs. Each item: name, price (INR), platform, reason.
# ---------------------------------------------------------------------------

HOME_CATALOG: dict[str, list[dict]] = {
    "Lighting": [
        {"name": "Philips LED Bulb 9W (Pack of 4)", "price": 450, "platform": "Amazon",
         "reason": "Energy-efficient everyday lighting with long bulb life."},
        {"name": "Wipro Garnet LED Downlight 7W", "price": 320, "platform": "Amazon",
         "reason": "Recessed ceiling light that gives rooms a clean, modern look."},
        {"name": "Syska LED Panel Light 12W", "price": 550, "platform": "Flipkart",
         "reason": "Slim panel light ideal for kitchens and study areas."},
        {"name": "IKEA SOLHETTA LED Bulb E27", "price": 180, "platform": "IKEA",
         "reason": "Affordable warm-white bulb for lamps and ceiling fixtures."},
        {"name": "Havells Luster Decorative Light", "price": 899, "platform": "Amazon",
         "reason": "Decorative accent light to elevate living-room ambience."},
        {"name": "IKEA HEKTAR Floor Lamp", "price": 2490, "platform": "IKEA",
         "reason": "Adjustable floor lamp that adds focused task lighting."},
        {"name": "Philips Hue White Ambiance E27", "price": 1299, "platform": "Amazon",
         "reason": "Smart bulb with adjustable warmth for mood lighting."},
        {"name": "Wipro Garnet LED Strip Light 5m", "price": 649, "platform": "Flipkart",
         "reason": "Flexible strip lighting for coves, beds and TV units."},
    ],
    "Fans": [
        {"name": "Orient Electric Apex Air 1200mm", "price": 1899, "platform": "Amazon",
         "reason": "High-air-delivery ceiling fan, reliable and quiet."},
        {"name": "Usha Mist Air 1200mm", "price": 1750, "platform": "Flipkart",
         "reason": "Energy-saving fan with a sleek, modern profile."},
        {"name": "Crompton Highspeed Torpedo 1200mm", "price": 2199, "platform": "Amazon",
         "reason": "Powerful airflow for larger rooms and living areas."},
        {"name": "IKEA STÄLL Ceiling Fan", "price": 3490, "platform": "IKEA",
         "reason": "Minimalist Scandinavian design that blends with decor."},
        {"name": "Havells V3 Yurbo 1200mm", "price": 2499, "platform": "Amazon",
         "reason": "Premium finish fan with smooth, vibration-free operation."},
        {"name": "Bajaj Elegance 1200mm", "price": 1599, "platform": "Flipkart",
         "reason": "Budget-friendly fan that does the job well."},
    ],
    "Tables": [
        {"name": "IKEA LACK Side Table", "price": 799, "platform": "IKEA",
         "reason": "Compact side table, perfect beside sofas and beds."},
        {"name": "IKEA LISABO Coffee Table", "price": 4990, "platform": "IKEA",
         "reason": "Elegant ash-veneer coffee table for the living room."},
        {"name": "Amazon Brand Solimo Study Table", "price": 2499, "platform": "Amazon",
         "reason": "Sturdy engineered-wood table for work and study."},
        {"name": "Flipkart SmartBuy Dining Table 4-Seater", "price": 5999, "platform": "Flipkart",
         "reason": "Family-sized dining table with a durable finish."},
        {"name": "Nilkamal Leo Engineered Wood Table", "price": 3299, "platform": "Amazon",
         "reason": "Versatile table suitable for dining or as a desk."},
        {"name": "IKEA NORDEN Gateleg Table", "price": 7990, "platform": "IKEA",
         "reason": "Extendable gateleg table that saves space when not in use."},
    ],
    "Sofas": [
        {"name": "IKEA KIVIK 2-Seater Sofa", "price": 24990, "platform": "IKEA",
         "reason": "Deep, comfortable seating with washable covers."},
        {"name": "Amazon Brand Solimo 3-Seater Fabric Sofa", "price": 12999, "platform": "Amazon",
         "reason": "Spacious 3-seater that anchors the living room."},
        {"name": "Flipkart SmartBuy 5-Seater L-Shape Sofa", "price": 18999, "platform": "Flipkart",
         "reason": "L-shaped sectional ideal for family movie nights."},
        {"name": "Nilkamal Sofia 3-Seater Sofa", "price": 15499, "platform": "Amazon",
         "reason": "Plush cushions and a contemporary silhouette."},
        {"name": "IKEA EKTORP 3-Seater", "price": 34990, "platform": "IKEA",
         "reason": "Classic design with reversible back cushions."},
        {"name": "Durian 2-Seater Fabric Sofa", "price": 11999, "platform": "Flipkart",
         "reason": "Compact 2-seater for smaller living spaces."},
    ],
    "Decor": [
        {"name": "IKEA FEJKA Artificial Potted Plant", "price": 499, "platform": "IKEA",
         "reason": "Low-maintenance greenery that freshens up any corner."},
        {"name": "Amazon Brand Solimo Wall Art Set (Set of 3)", "price": 899, "platform": "Amazon",
         "reason": "Coordinated wall art that ties a room together."},
        {"name": "Flipkart SmartBuy Photo Frames (Set of 6)", "price": 599, "platform": "Flipkart",
         "reason": "Gallery-wall frames for personal memories."},
        {"name": "IKEA RIBBA Frame 50x50cm", "price": 349, "platform": "IKEA",
         "reason": "Clean, modern frame for prints and posters."},
        {"name": "Homesake Metal Wall Decor", "price": 1299, "platform": "Amazon",
         "reason": "Statement metal piece for an accent wall."},
        {"name": "IKEA STOCKHOLM Mirror", "price": 3990, "platform": "IKEA",
         "reason": "Large mirror that makes rooms feel brighter and bigger."},
        {"name": "ArtStreet Canvas Painting", "price": 1499, "platform": "Amazon",
         "reason": "Hand-painted canvas that adds colour and character."},
        {"name": "IKEA SINNLIG Scented Candle", "price": 249, "platform": "IKEA",
         "reason": "Subtle fragrance for a warm, welcoming home."},
    ],
    "Flooring": [
        {"name": "IKEA STOEN Rug", "price": 1290, "platform": "IKEA",
         "reason": "Soft rug that defines a seating area."},
        {"name": "Amazon Brand Solimo Polypropylene Rug", "price": 1499, "platform": "Amazon",
         "reason": "Durable, easy-clean rug for high-traffic zones."},
        {"name": "Flipkart SmartBuy Floor Mat", "price": 799, "platform": "Flipkart",
         "reason": "Comfortable mat for bedrooms and living rooms."},
    ],
    "Storage": [
        {"name": "IKEA KALLAX Shelf Unit", "price": 5990, "platform": "IKEA",
         "reason": "Modular shelving for books, decor and essentials."},
        {"name": "Amazon Brand Solimo 5-Shelf Bookcase", "price": 3499, "platform": "Amazon",
         "reason": "Tall bookcase that maximises vertical storage."},
        {"name": "Nilkamal Freedom Mini Chest", "price": 2999, "platform": "Flipkart",
         "reason": "Compact chest of drawers for clutter-free rooms."},
    ],
    "Textiles": [
        {"name": "IKEA VINDUM Rug", "price": 2490, "platform": "IKEA",
         "reason": "Thick, cozy rug for underfoot comfort."},
        {"name": "Amazon Brand Solimo Cotton Bedsheet Set", "price": 899, "platform": "Amazon",
         "reason": "Breathable cotton bedding for a fresh night's sleep."},
        {"name": "Flipkart SmartBuy Cushion Covers (Pack of 5)", "price": 499, "platform": "Flipkart",
         "reason": "Quick, affordable way to refresh sofa styling."},
    ],
}

PARTY_CATALOG: dict[str, list[dict]] = {
    "Catering": [
        {"name": "Swiggy South Indian Buffet (per plate)", "price": 299, "platform": "Swiggy",
         "reason": "Crowd-pleasing vegetarian buffet, ordered per plate."},
        {"name": "Zomato North Indian Thali (per plate)", "price": 349, "platform": "Zomato",
         "reason": "Hearty thali with curries, roti and dessert."},
        {"name": "Swiggy Chinese Combo (per plate)", "price": 279, "platform": "Swiggy",
         "reason": "Popular Indo-Chinese spread guests love."},
        {"name": "Zomato Dessert Counter (per plate)", "price": 199, "platform": "Zomato",
         "reason": "Sweet finish with cakes, pastries and ice cream."},
        {"name": "Swiggy Biryani Special (per plate)", "price": 249, "platform": "Swiggy",
         "reason": "Aromatic biryani that works as a main course."},
    ],
    "Decorations": [
        {"name": "Amazon Balloon Decoration Kit", "price": 599, "platform": "Amazon",
         "reason": "Complete balloon setup for instant festive vibes."},
        {"name": "Flipkart LED Fairy Lights 10m", "price": 349, "platform": "Flipkart",
         "reason": "Warm string lights that transform any venue."},
        {"name": "Amazon Theme Party Decor Set", "price": 1299, "platform": "Amazon",
         "reason": "Coordinated theme decor for a polished look."},
        {"name": "Flipkart Paper Bunting & Banner Set", "price": 249, "platform": "Flipkart",
         "reason": "Cheerful banners and buntings for entrances."},
        {"name": "Amazon Table Centerpiece Set", "price": 449, "platform": "Amazon",
         "reason": "Elegant centerpieces that dress up dining tables."},
    ],
    "Entertainment": [
        {"name": "BookMyShow Movie Tickets (per person)", "price": 250, "platform": "BookMyShow",
         "reason": "Group movie outing — simple, fun entertainment."},
        {"name": "Amazon Bluetooth Party Speaker", "price": 2499, "platform": "Amazon",
         "reason": "Portable speaker for music and announcements."},
        {"name": "Flipkart Karaoke Microphone Set", "price": 1199, "platform": "Flipkart",
         "reason": "Karaoke set that gets guests involved."},
        {"name": "Local DJ 4-Hour Package", "price": 8000, "platform": "BookMyShow",
         "reason": "Professional DJ for dancing and crowd energy."},
    ],
    "Venue/Accommodation": [
        {"name": "OYO Standard Room (per night)", "price": 1499, "platform": "OYO",
         "reason": "Clean, affordable stay for out-of-town guests."},
        {"name": "OYO Premium Suite (per night)", "price": 2499, "platform": "OYO",
         "reason": "Spacious suite for the host or VIP guests."},
        {"name": "Local Banquet Hall (4 hours)", "price": 15000, "platform": "OYO",
         "reason": "Dedicated venue for larger celebrations."},
        {"name": "OYO Family Room (per night)", "price": 1999, "platform": "OYO",
         "reason": "Roomy option for families attending the event."},
    ],
    "Photography": [
        {"name": "Local Photographer 4-Hour Package", "price": 6000, "platform": "BookMyShow",
         "reason": "Capture memories with a professional photographer."},
        {"name": "Amazon Instant Camera + Film", "price": 4999, "platform": "Amazon",
         "reason": "Fun instant prints guests can take home."},
    ],
    "Gifts": [
        {"name": "Amazon Return Gift Hamper (per piece)", "price": 149, "platform": "Amazon",
         "reason": "Thoughtful token of appreciation for guests."},
        {"name": "Flipkart Chocolate Box (per piece)", "price": 199, "platform": "Flipkart",
         "reason": "Sweet, universally loved return gift."},
    ],
}

JEWELRY_CATALOG: dict[str, list[dict]] = {
    "Earrings": [
        {"name": "Tanishq Gold-Plated Jhumka Earrings", "price": 2499, "platform": "Amazon",
         "reason": "Classic jhumkas that pair well with ethnic outfits."},
        {"name": "Zaveri Pearls Kundan Stud Earrings", "price": 1299, "platform": "Flipkart",
         "reason": "Elegant kundan studs for a refined look."},
        {"name": "Myntra Oxidised Silver Jhumkas", "price": 899, "platform": "Myntra",
         "reason": "Boho-chic oxidised jhumkas for everyday wear."},
        {"name": "Amazon Pearl Drop Earrings", "price": 1099, "platform": "Amazon",
         "reason": "Delicate pearl drops that suit both ethnic and western wear."},
        {"name": "Flipkart Gold-Plated Chandbalis", "price": 1499, "platform": "Flipkart",
         "reason": "Crescent-shaped chandbalis with traditional charm."},
    ],
    "Necklaces": [
        {"name": "Tanishq Rivaah Gold Necklace", "price": 18999, "platform": "Amazon",
         "reason": "Statement necklace for weddings and grand occasions."},
        {"name": "Zaveri Pearls Temple Necklace", "price": 2999, "platform": "Flipkart",
         "reason": "Temple-inspired design with intricate detailing."},
        {"name": "Myntra Layered Chain Necklace", "price": 1199, "platform": "Myntra",
         "reason": "Trendy layered chains for contemporary outfits."},
        {"name": "Amazon Kundan Choker Set", "price": 1799, "platform": "Amazon",
         "reason": "Regal choker that elevates festive attire."},
        {"name": "Flipkart Pearl Rani Haar", "price": 2499, "platform": "Flipkart",
         "reason": "Long rani haar for a royal, traditional statement."},
    ],
    "Bracelets": [
        {"name": "Amazon Gold-Plated Bangle Set", "price": 999, "platform": "Amazon",
         "reason": "Stackable bangles that complete ethnic ensembles."},
        {"name": "Flipkart Charm Bracelet", "price": 699, "platform": "Flipkart",
         "reason": "Playful charm bracelet for casual, daily wear."},
        {"name": "Myntra Kundan Kada", "price": 1299, "platform": "Myntra",
         "reason": "Ornate kada that adds sparkle to any outfit."},
    ],
    "Rings": [
        {"name": "Amazon Solitaire Ring", "price": 1499, "platform": "Amazon",
         "reason": "Timeless solitaire that works for parties and daily wear."},
        {"name": "Flipkart Cocktail Ring Set", "price": 799, "platform": "Flipkart",
         "reason": "Bold cocktail rings to accessorise western outfits."},
        {"name": "Myntra Minimalist Band Ring", "price": 599, "platform": "Myntra",
         "reason": "Sleek band for an understated, modern touch."},
    ],
    "Bangles": [
        {"name": "Amazon Glass Bangles (Set of 12)", "price": 499, "platform": "Amazon",
         "reason": "Colourful glass bangles for festive occasions."},
        {"name": "Flipkart Gold-Plated Kada Set", "price": 1199, "platform": "Flipkart",
         "reason": "Traditional kada set with a polished finish."},
        {"name": "Myntra Pearl Bracelet", "price": 899, "platform": "Myntra",
         "reason": "Elegant pearl bracelet for subtle sophistication."},
    ],
    "Sets": [
        {"name": "Tanishq Rivaah Bridal Set", "price": 24999, "platform": "Amazon",
         "reason": "Complete bridal set for the most special occasions."},
        {"name": "Zaveri Pearls Wedding Set", "price": 4999, "platform": "Flipkart",
         "reason": "Coordinated wedding set with necklace and earrings."},
        {"name": "Amazon Festive Jewelry Combo", "price": 2299, "platform": "Amazon",
         "reason": "Value combo covering multiple pieces for festive looks."},
    ],
}

# Preferred jewelry categories keyed by common jewelry_type inputs.
JEWELRY_TYPE_MAP = {
    "earrings": ["Earrings"],
    "necklace": ["Necklaces"],
    "necklaces": ["Necklaces"],
    "bracelet": ["Bracelets"],
    "bracelets": ["Bracelets"],
    "ring": ["Rings"],
    "rings": ["Rings"],
    "bangles": ["Bangles"],
    "bangle": ["Bangles"],
    "set": ["Sets"],
    "sets": ["Sets"],
    "bridal": ["Sets", "Necklaces", "Earrings"],
    "wedding": ["Sets", "Necklaces", "Earrings"],
    "daily": ["Earrings", "Rings", "Bracelets"],
    "office": ["Earrings", "Rings"],
    "party": ["Earrings", "Necklaces", "Rings"],
    "festive": ["Earrings", "Necklaces", "Bangles"],
}


# ---------------------------------------------------------------------------
# Selection helpers
# ---------------------------------------------------------------------------

def _spread_indices(n: int, count: int) -> list[int]:
    """Return up to `count` indices spread across the sorted item list."""
    if n <= 0 or count <= 0:
        return []
    if n <= count:
        return list(range(n))
    if count == 1:
        return [n // 2]
    step = (n - 1) / (count - 1)
    return sorted({round(i * step) for i in range(count)})


def _pick_items(items: list[dict], count: int, category_budget: float) -> list[dict]:
    """Pick up to `count` items within `category_budget`, mixing price points."""
    if not items or count <= 0 or category_budget <= 0:
        return []
    sorted_items = sorted(items, key=lambda x: x["price"])
    selected: list[dict] = []
    remaining = category_budget

    for idx in _spread_indices(len(sorted_items), count):
        item = sorted_items[idx]
        if item["price"] <= remaining:
            selected.append(item)
            remaining -= item["price"]

    # Fill any gaps with the cheapest items that still fit.
    if len(selected) < count:
        for item in sorted_items:
            if len(selected) >= count:
                break
            if item not in selected and item["price"] <= remaining:
                selected.append(item)
                remaining -= item["price"]
    return selected


def _to_items(picked: list[dict], category: str) -> list[RecommendationItem]:
    return [
        RecommendationItem(
            name=i["name"],
            category=category,
            price=i["price"],
            platform=i["platform"],
            reason=i["reason"],
            url=build_link(i["platform"], i["name"]),
        )
        for i in picked
    ]


def _contingency(budget: float) -> float:
    return round(budget * settings.CONTINGENCY_PERCENT / 100, 2)


def _finish(
    planner_type: str,
    title: str,
    budget: float,
    currency: str,
    categories: list[CategoryAllocation],
    source: str,
    notes: Optional[str] = None,
) -> PlanResult:
    contingency = _contingency(budget)
    allocated = round(sum(c.subtotal for c in categories), 2)
    remaining = round(budget - allocated - contingency, 2)
    warnings: list[str] = []
    if remaining < 0:
        warnings.append(
            f"Plan exceeds budget by ₹{abs(remaining):,.2f} even after the "
            f"{settings.CONTINGENCY_PERCENT:.0f}% contingency reserve."
        )
    elif remaining < budget * 0.02:
        warnings.append("Very little buffer remains after the contingency reserve.")
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
        source=source,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Planner builders (deterministic mock engine)
# ---------------------------------------------------------------------------

def build_home_plan(
    budget: float,
    rooms: list[str],
    style: str,
    quantities: dict[str, int],
    currency: str = "INR",
) -> PlanResult:
    contingency = _contingency(budget)
    available = budget - contingency
    room_count = max(len(rooms), 1)

    desired = {
        "Lighting": max(quantities.get("lights", 0), room_count),
        "Fans": max(quantities.get("fans", 0), room_count),
        "Tables": max(quantities.get("tables", 0), 1),
        "Sofas": max(quantities.get("sofas", 0), 1),
        "Decor": max(quantities.get("decor", 0), 2),
        "Flooring": 1,
        "Storage": 1,
        "Textiles": 1,
    }
    weights = {cat: max(cnt, 1) for cat, cnt in desired.items()}
    total_weight = sum(weights.values())
    allocations = {cat: available * w / total_weight for cat, w in weights.items()}

    categories: list[CategoryAllocation] = []
    for cat, items in HOME_CATALOG.items():
        picked = _pick_items(items, desired.get(cat, 1), allocations.get(cat, 0))
        if picked:
            categories.append(
                CategoryAllocation(category=cat, items=_to_items(picked, cat), subtotal=round(sum(i["price"] for i in picked), 2))
            )

    # Top up with extra decor/textiles/storage while budget allows, merging
    # into existing category entries to avoid duplicates.
    allocated = sum(c.subtotal for c in categories)
    for cat in ("Decor", "Textiles", "Storage", "Lighting"):
        if allocated >= available * 0.97:
            break
        existing = {i.name for c in categories if c.category == cat for i in c.items}
        for item in sorted(HOME_CATALOG[cat], key=lambda x: x["price"]):
            if item["name"] not in existing and allocated + item["price"] <= available:
                for c in categories:
                    if c.category == cat:
                        c.items.append(_to_items([item], cat)[0])
                        c.subtotal = round(c.subtotal + item["price"], 2)
                        break
                allocated += item["price"]
                break

    title = f"{style.title()} home plan for {room_count} room{'s' if room_count > 1 else ''}"
    return _finish("home", title, budget, currency, categories, "demo")


def build_party_plan(
    budget: float,
    guest_count: int,
    event_type: str,
    venue_preference: str,
    location: str,
    currency: str = "INR",
) -> PlanResult:
    contingency = _contingency(budget)
    available = budget - contingency

    weights = {
        "Catering": 40,
        "Venue/Accommodation": 25,
        "Decorations": 15,
        "Entertainment": 12,
        "Photography": 5,
        "Gifts": 3,
    }
    allocations = {cat: available * w / 100 for cat, w in weights.items()}
    categories: list[CategoryAllocation] = []

    # Catering: per-plate option that best fits the allocation.
    catering_options = sorted(PARTY_CATALOG["Catering"], key=lambda x: x["price"])
    catering_pick = None
    for opt in catering_options:
        if opt["price"] * guest_count <= allocations["Catering"]:
            catering_pick = opt
    if catering_pick is None and catering_options:
        catering_pick = catering_options[0]
    if catering_pick:
        total = round(catering_pick["price"] * guest_count, 2)
        item = RecommendationItem(
            name=f"{catering_pick['name']} × {guest_count} guests",
            category="Catering",
            price=total,
            platform=catering_pick["platform"],
            reason=catering_pick["reason"],
            url=build_link(catering_pick["platform"], catering_pick["name"], location),
        )
        categories.append(CategoryAllocation(category="Catering", items=[item], subtotal=total))

    # Venue: single best-fit option.
    venue_options = sorted(PARTY_CATALOG["Venue/Accommodation"], key=lambda x: x["price"])
    venue_pick = None
    for opt in venue_options:
        if opt["price"] <= allocations["Venue/Accommodation"]:
            venue_pick = opt
    if venue_pick is None and venue_options:
        venue_pick = venue_options[0]
    if venue_pick:
        item = RecommendationItem(
            name=venue_pick["name"],
            category="Venue/Accommodation",
            price=venue_pick["price"],
            platform=venue_pick["platform"],
            reason=venue_pick["reason"],
            url=build_link(venue_pick["platform"], venue_pick["name"], location),
        )
        categories.append(CategoryAllocation(category="Venue/Accommodation", items=[item], subtotal=venue_pick["price"]))

    # Decorations & entertainment: 1-2 items each.
    for cat, count in (("Decorations", 2), ("Entertainment", 2), ("Photography", 1)):
        picked = _pick_items(PARTY_CATALOG[cat], count, allocations.get(cat, 0))
        if picked:
            categories.append(CategoryAllocation(category=cat, items=_to_items(picked, cat), subtotal=round(sum(i["price"] for i in picked), 2)))

    # Gifts: per-piece × guests if it fits.
    gift_options = sorted(PARTY_CATALOG["Gifts"], key=lambda x: x["price"])
    for opt in gift_options:
        total = opt["price"] * guest_count
        if total <= allocations["Gifts"]:
            item = RecommendationItem(
                name=f"{opt['name']} × {guest_count} guests",
                category="Gifts",
                price=round(total, 2),
                platform=opt["platform"],
                reason=opt["reason"],
                url=build_link(opt["platform"], opt["name"]),
            )
            categories.append(CategoryAllocation(category="Gifts", items=[item], subtotal=round(total, 2)))
            break

    title = f"{event_type.title()} for {guest_count} guests in {location}"
    return _finish("party", title, budget, currency, categories, "demo")


def build_jewelry_plan(
    budget: float,
    occasion: str,
    jewelry_type: str,
    style_preference: str,
    currency: str = "INR",
    outfit_analysis: Optional[str] = None,
) -> PlanResult:
    contingency = _contingency(budget)
    available = budget - contingency

    preferred = JEWELRY_TYPE_MAP.get(jewelry_type.lower(), ["Earrings", "Necklaces", "Bracelets"])
    categories: list[CategoryAllocation] = []
    allocated = 0.0

    # Primary item from the preferred category.
    primary_cat = preferred[0]
    primary_options = sorted(JEWELRY_CATALOG[primary_cat], key=lambda x: x["price"])
    primary_pick = None
    for opt in primary_options:
        if opt["price"] <= available * 0.6:
            primary_pick = opt
    if primary_pick is None and primary_options:
        primary_pick = primary_options[0]
    if primary_pick:
        categories.append(CategoryAllocation(category=primary_cat, items=_to_items([primary_pick], primary_cat), subtotal=primary_pick["price"]))
        allocated += primary_pick["price"]

    # Complementary pieces from other categories while budget allows.
    for cat in preferred[1:]:
        if allocated >= available * 0.85:
            break
        options = sorted(JEWELRY_CATALOG[cat], key=lambda x: x["price"])
        for opt in options:
            if allocated + opt["price"] <= available:
                categories.append(CategoryAllocation(category=cat, items=_to_items([opt], cat), subtotal=opt["price"]))
                allocated += opt["price"]
                break

    notes = None
    if outfit_analysis:
        notes = f"Outfit analysis: {outfit_analysis}"

    title = f"{occasion.title()} {jewelry_type.lower()} in {style_preference.lower()} style"
    return _finish("jewelry", title, budget, currency, categories, "demo", notes=notes)
