"""
FastAPI application entry-point.
CORS is configured for local React (Vite) development.
All endpoints perform real async CRUD against Supabase via SQLAlchemy 2.0.
"""

import uuid
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Grant, GrantMatch, Organization
from backend.schemas import (
    GrantMatchOut,
    GrantOut,
    OrganizationCreate,
    OrganizationOut,
)

logger = logging.getLogger(__name__)

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
@app.post(
    "/api/organizations",
    response_model=OrganizationOut,
    status_code=201,
    tags=["organizations"],
)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new nonprofit organization profile."""
    try:
        org = Organization(**payload.model_dump())
        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org
    except IntegrityError as exc:
        await db.rollback()
        logger.error("Integrity error creating organization: %s", exc)
        raise HTTPException(status_code=409, detail="Organization already exists.")
    except SQLAlchemyError as exc:
        await db.rollback()
        logger.error("DB error creating organization: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create organization.")


@app.get(
    "/api/organizations",
    response_model=list[OrganizationOut],
    tags=["organizations"],
)
async def list_organizations(
    db: AsyncSession = Depends(get_db),
):
    """Return all registered organizations."""
    try:
        result = await db.execute(select(Organization))
        return result.scalars().all()
    except SQLAlchemyError as exc:
        logger.error("DB error listing organizations: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch organizations.")


@app.get(
    "/api/organizations/{org_id}",
    response_model=OrganizationOut,
    tags=["organizations"],
)
async def get_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single organization by ID."""
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalars().first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found.")
        return org
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error("DB error fetching organization %s: %s", org_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch organization.")


# ── Grants ───────────────────────────────────────────────────────────────────
@app.get(
    "/api/grants",
    response_model=list[GrantOut],
    tags=["grants"],
)
async def list_grants(
    db: AsyncSession = Depends(get_db),
):
    """Return all scraped grant opportunities."""
    try:
        result = await db.execute(select(Grant))
        return result.scalars().all()
    except SQLAlchemyError as exc:
        logger.error("DB error listing grants: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch grants.")


# ── Matches ──────────────────────────────────────────────────────────────────
@app.get(
    "/api/matches",
    response_model=list[GrantMatchOut],
    tags=["matches"],
)
async def list_matches(
    db: AsyncSession = Depends(get_db),
):
    """Return all grant ↔ organization match results."""
    try:
        result = await db.execute(select(GrantMatch))
        return result.scalars().all()
    except SQLAlchemyError as exc:
        logger.error("DB error listing matches: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch matches.")


# ── Admin: Scrape Trigger ────────────────────────────────────────────────────
@app.post("/api/admin/scrape", tags=["admin"])
async def trigger_scrape():
    """
    Kick off the full scraping pipeline (Grants.gov + RWJF).
    Returns a summary with counts of scraped, saved, and errored grants.
    """
    from scraper.pipeline import ScrapePipeline

    try:
        pipeline = ScrapePipeline()
        summary = await pipeline.run()
        return summary
    except Exception as exc:
        logger.error("Scraping pipeline failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Scraping pipeline failed: {exc}",
        )

