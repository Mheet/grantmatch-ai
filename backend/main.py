"""
FastAPI application entry-point.
CORS is configured for local React (Vite) development.
Placeholder endpoints will be fleshed out in subsequent blocks.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas import (
    GrantMatchOut,
    GrantOut,
    OrganizationCreate,
    OrganizationOut,
)

app = FastAPI(
    title="Grant Opportunity Finder",
    description="Crawl foundation databases, match grants to nonprofit missions, and draft LOIs.",
    version="0.1.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
async def health_check():
    """Quick liveness probe."""
    return {"status": "ok"}


# ── Organizations ────────────────────────────────────────────────────────────
@app.post("/api/organizations", response_model=dict, tags=["organizations"])
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new nonprofit organization profile."""
    return {"message": "Not implemented yet"}


@app.get("/api/organizations", response_model=dict, tags=["organizations"])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
):
    """Return all registered organizations."""
    return {"message": "Not implemented yet"}


# ── Grants ───────────────────────────────────────────────────────────────────
@app.get("/api/grants", response_model=dict, tags=["grants"])
async def list_grants(
    db: AsyncSession = Depends(get_db),
):
    """Return all scraped grant opportunities."""
    return {"message": "Not implemented yet"}


# ── Matches ──────────────────────────────────────────────────────────────────
@app.get("/api/matches", response_model=dict, tags=["matches"])
async def list_matches(
    db: AsyncSession = Depends(get_db),
):
    """Return all grant ↔ organization match results."""
    return {"message": "Not implemented yet"}
