from fastapi import FastAPI, HTTPException

from app.connectors.github import fetch_contributions

app = FastAPI(title="DevDigest API")


@app.get("/")
def root():
    return {"app": "DevDigest API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


# Temporary route for local testing only. Remove before deploying.
@app.get("/debug/github")
async def debug_github(days: int = 7):
    if not 1 <= days <= 365:
        raise HTTPException(status_code=400, detail="days must be between 1 and 365")
    try:
        return await fetch_contributions(days)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))