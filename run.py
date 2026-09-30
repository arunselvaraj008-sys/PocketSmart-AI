"""Convenience launcher for PocketSmart AI.

The app can also be started directly with:
    uvicorn app.main:app --reload
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
