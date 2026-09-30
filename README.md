# PocketSmart AI

A budget-aware AI recommendation assistant with three planners — **Home Interior**, **Party Budget**, and **Jewelry** — built with FastAPI, Jinja2, SQLAlchemy, and an optional Google Gemini integration.

Every plan respects your budget, holds back a configurable contingency reserve, and returns clear, shoppable recommendation cards with simulated links to Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO and more.

---

## Features

- **Three smart planners**
  - **Home Interior** — budget, rooms, style, and item quantities → room-by-room allocation with lights, fans, tables, sofas, decor and more.
  - **Party Budget** — budget, guest count, event type, venue and location → categorized plan for catering, decorations, entertainment, venue/accommodation and gifts.
  - **Jewelry** — budget, occasion, jewelry type and style → coordinated picks, with optional outfit-image upload for AI vision styling advice.
- **Budget-first design** — every plan shows total, allocated, contingency and remaining amounts, with warnings when a plan exceeds budget.
- **Demo mode** — runs fully without an API key using high-quality deterministic mock recommendations. Clearly labelled "Demo recommendations".
- **Optional Gemini** — when `GEMINI_API_KEY` is set, plans are AI-enhanced via the official Google GenAI SDK (strict JSON, validated, with automatic fallback to the mock engine).
- **Accounts & history** — register, login, logout, protected dashboard, and a per-user recommendation history with view/delete.
- **Secure** — bcrypt password hashing, JWT bearer tokens (httpOnly cookie + Authorization header), input validation, file-upload limits, and safe image handling (type + magic-byte checks).
- **Responsive UI** — polished, mobile-friendly design with empty, loading, validation, API-error and demo-mode states.

---

## Prerequisites

- Python 3.11+
- pip

---

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set a strong SECRET_KEY. GEMINI_API_KEY is optional.
```

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes (prod) | `dev-secret-key-change-in-production` | JWT signing key. Use a long random string in production. |
| `DATABASE_URL` | No | `sqlite:///./pocketsmart.db` | SQLAlchemy database URL. |
| `GEMINI_API_KEY` | No | _(empty)_ | Google Gemini API key. Leave empty for demo mode. |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model name. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | JWT lifetime in minutes. |
| `CONTINGENCY_PERCENT` | No | `10` | Contingency reserve held back from every plan. |
| `ALLOWED_ORIGINS` | No | `http://localhost:8000,http://127.0.0.1:8000` | Comma-separated CORS origins. |
| `MAX_UPLOAD_SIZE_MB` | No | `5` | Max jewelry image upload size in MB. |
| `UPLOAD_DIR` | No | `app/static/uploads` | Directory for uploaded outfit images. |

---

## Running the app

```bash
# From the project root (pocketsmart-ai/)
uvicorn app.main:app --reload
```

Then open **http://127.0.0.1:8000**.

You can also use the convenience launcher:

```bash
python run.py
```

---

## Demo mode behavior

Without `GEMINI_API_KEY` (or without the `google-genai` package installed):

- The app runs entirely on the deterministic mock engine.
- All plans are marked with a **"Demo recommendations"** badge.
- Jewelry outfit images are accepted and validated but not analyzed (no vision call).
- Every plan is still budget-aware, category-allocated, and contingency-reserved.

When `GEMINI_API_KEY` is configured:

- The app asks Gemini for a strict-JSON plan built only from the mock catalog.
- Responses are validated (known items, matching prices, within budget). Malformed or over-budget responses are rejected and the app falls back to the mock engine.
- Valid plans are marked **"AI-enhanced"**.
- Jewelry outfit images are analyzed with Gemini vision for styling notes.

---

## Running tests

```bash
pytest tests/ -v
```

The suite covers authentication, planner validation, mock fallback, budget totals, image-upload validation, and history access isolation. Tests run against an isolated SQLite database and force demo mode (no API key required).

---

## API endpoint summary

### Auth
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create an account |
| `POST` | `/api/auth/login` | Log in (sets httpOnly cookie, returns JWT) |
| `POST` | `/api/auth/logout` | Log out (clears cookie) |
| `GET` | `/api/auth/me` | Current authenticated user |

### Planners (protected)
| Method | Path | Description |
|---|---|---|
| `POST` | `/api/planners/home` | Generate a home interior plan |
| `POST` | `/api/planners/party` | Generate a party budget plan |
| `POST` | `/api/planners/jewelry` | Generate a jewelry plan (multipart, optional image) |

### History (protected)
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/history` | List the current user's plans |
| `GET` | `/api/history/{id}` | View a single plan |
| `DELETE` | `/api/history/{id}` | Delete a plan |

### Pages
| Path | Description |
|---|---|
| `/` | Landing page |
| `/login`, `/register` | Auth pages |
| `/dashboard` | Protected user dashboard |
| `/planners/home`, `/planners/party`, `/planners/jewelry` | Planner pages |
| `/results/{id}` | Plan results |
| `/history` | Recommendation history |
| `/testimonials` | Testimonials |

---

## Project structure

```
pocketsmart-ai/
  app/
    main.py                  # App factory & entry point
    core/
      config.py              # Settings (env / .env)
      security.py            # Password hashing, JWT, current-user dependency
      database.py            # Engine, session, get_db
      templating.py          # Jinja2 templates instance
    models/
      user.py                # User model
      recommendation.py      # RecommendationHistory model
    schemas/
      auth.py                # Auth schemas
      planners.py            # Planner request schemas
      recommendation.py       # Plan/result schemas
    routers/
      auth.py                # Auth API
      pages.py               # Jinja page routes
      planners.py             # Planner API
      history.py             # History API
    services/
      gemini_service.py      # Google GenAI SDK integration (lazy, optional)
      recommendation_service.py  # Orchestration: mock + Gemini
      provider_service.py    # Provider link abstraction (simulated)
      mock_catalog_service.py    # Deterministic mock engine & catalog
    templates/               # Jinja2 templates
    static/
      css/style.css
      js/app.js
      uploads/               # Uploaded outfit images
  tests/
    conftest.py
    test_auth.py
    test_planners.py
    test_history.py
  requirements.txt
  .env.example
  README.md
  run.py
```

---

## Notes

- All external product/service links are **simulated** search URLs for demonstration. No sites are scraped and no live prices are fetched.
- To integrate licensed APIs later, replace `build_link` in `provider_service.py` and the mock catalog lookups — the rest of the app is unaffected.
- Set a strong `SECRET_KEY` before deploying to production.
