"""Provider abstraction for external recommendation links.

All links are clearly labelled, simulated search URLs — no scraping and no
live price lookups. To integrate licensed APIs later, replace `build_link`
with real provider calls; the rest of the app is unaffected.
"""
import urllib.parse

PROVIDER_URL_TEMPLATES = {
    "Amazon": "https://www.amazon.in/s?k={query}",
    "Flipkart": "https://www.flipkart.com/search?q={query}",
    "IKEA": "https://www.ikea.com/in/en/search/?q={query}",
    "Swiggy": "https://www.swiggy.com/search?query={query}",
    "Zomato": "https://www.zomato.com/{location}/restaurants?query={query}",
    "OYO": "https://www.oyorooms.com/search?location={location}&query={query}",
    "Myntra": "https://www.myntra.com/{query}",
    "BookMyShow": "https://in.bookmyshow.com/search/{query}",
}

FALLBACK_TEMPLATE = "https://www.google.com/search?q={query}"


def _slug(text: str) -> str:
    return urllib.parse.quote_plus(text.strip())


def build_link(platform: str, query: str, location: str = "") -> str:
    """Build a clearly-labelled simulated search link for a provider."""
    template = PROVIDER_URL_TEMPLATES.get(platform, FALLBACK_TEMPLATE)
    try:
        return template.format(query=_slug(query), location=_slug(location))
    except (KeyError, IndexError):
        return FALLBACK_TEMPLATE.format(query=_slug(query))
