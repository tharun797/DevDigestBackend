from fastapi import FastAPI, HTTPException

from app.facts.extract import extract_facts

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


@app.get("/debug/facts")
async def debug_facts(days: int = 30):
    if not 1 <= days <= 180:
        raise HTTPException(status_code=400, detail="days must be between 1 and 180")
    try:
        current = await fetch_contributions(days)
        previous = await fetch_contributions(days, offset_days=days)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return extract_facts(current, previous, days)