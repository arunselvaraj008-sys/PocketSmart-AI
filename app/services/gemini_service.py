"""Google Gemini integration via the official Google GenAI SDK.

The SDK is imported lazily so the application runs in demo mode even when
`google-genai` is not installed or no API key is configured. Every call is
best-effort: on any failure the service returns None and the caller falls
back to the deterministic mock engine.
"""
import json
import re
import time
from typing import Optional

from app.core.config import settings

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0


def is_available() -> bool:
    """True when an API key is configured and the SDK is importable."""
    if not settings.GEMINI_API_KEY:
        return False
    try:
        import google.genai  # noqa: F401
        return True
    except ImportError:
        return False


def _get_client():
    from google import genai

    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _parse_json(text: str) -> Optional[dict]:
    """Parse strict JSON, stripping markdown fences and repairing common issues."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return data if isinstance(data, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def _with_retry(fn):
    """Retry a Gemini call on transient errors (503 high demand, 429 quota)."""
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except Exception as e:
            status = getattr(e, "status_code", None)
            transient = status in (429, 503, 500, 502, 504) or "UNAVAILABLE" in str(e).upper()
            if transient and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS * (attempt + 1))
                continue
            return None
    return None


def generate_plan_json(prompt: str) -> Optional[dict]:
    """Ask Gemini for a strict-JSON plan. Returns a parsed dict or None."""
    if not is_available():
        return None

    def _call():
        from google.genai import types

        client = _get_client()
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        )
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        return _parse_json(response.text or "")

    return _with_retry(_call)


def analyze_outfit_image(image_bytes: bytes, mime_type: str, prompt: str) -> Optional[str]:
    """Run a vision request over an uploaded outfit image. Returns text or None."""
    if not is_available():
        return None

    def _call():
        from google.genai import types

        client = _get_client()
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        config = types.GenerateContentConfig(temperature=0.3)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[prompt, part],
            config=config,
        )
        return (response.text or "").strip() or None

    return _with_retry(_call)
