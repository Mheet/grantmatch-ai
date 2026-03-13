"""
FastAPI application entry-point.
CORS is configured for local React (Vite) development.
All endpoints perform real async CRUD against Supabase via SQLAlchemy 2.0.
"""

import os
import uuid
import logging

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Grant, GrantMatch, Organization
from backend.schemas import (
    GrantMatchOut,
    GrantOut,
    MatchWithGrantOut,
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
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "https://grantmatch-ai.vercel.app"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    "/api/organizations/me",
    response_model=OrganizationOut,
    tags=["organizations"],
)
async def get_my_organization(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Look up the organization belonging to the authenticated Supabase user."""
    import jwt as pyjwt

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth token.")

    token = auth_header.split(" ", 1)[1]
    try:
        payload = pyjwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token.")

    if not user_id:
        raise HTTPException(status_code=401, detail="No user ID in token.")

    try:
        result = await db.execute(
            select(Organization).where(Organization.user_id == user_id)
        )
        org = result.scalars().first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found.")
        return org
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error("DB error fetching org for user %s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch organization.")


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


# ── Match Generation ─────────────────────────────────────────────────────────
@app.post("/api/matches/generate/{org_id}", tags=["matches"])
async def generate_matches(org_id: str):
    """
    Trigger Gemini-powered semantic matching for all unmatched grants
    against the specified organization.
    """
    from backend.services.matcher import run_matching_for_org

    try:
        summary = await run_matching_for_org(org_id)
        return summary
    except Exception as exc:
        logger.error("Match generation failed for org %s: %s", org_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Match generation failed: {exc}",
        )


# ── Matches for an Organization ──────────────────────────────────────────────
@app.get(
    "/api/matches/{org_id}",
    response_model=list[MatchWithGrantOut],
    tags=["matches"],
)
async def get_org_matches(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Return all matches for an organization, sorted by score descending, with full grant details."""
    try:
        result = await db.execute(
            select(GrantMatch)
            .where(GrantMatch.organization_id == org_id)
            .options(selectinload(GrantMatch.grant))
            .order_by(GrantMatch.match_score.desc())
        )
        return result.scalars().all()
    except SQLAlchemyError as exc:
        logger.error("DB error fetching matches for org %s: %s", org_id, exc)
        raise HTTPException(status_code=500, detail="Failed to fetch matches.")


# ── LOI Generation ───────────────────────────────────────────────────────────
@app.post("/api/loi/generate/{match_id}", tags=["loi"])
async def generate_loi_endpoint(match_id: uuid.UUID):
    """Generate a Letter of Intent for a specific grant match."""
    from backend.services.writer import generate_loi
    from backend.database import async_session
    import json as _json

    try:
        # ── Session 1: Fetch data (short-lived) ─────────────────────────
        async with async_session() as db:
            result = await db.execute(
                select(GrantMatch).where(GrantMatch.id == match_id)
            )
            match = result.scalars().first()
            if not match:
                raise HTTPException(status_code=404, detail="Match not found.")

            org_result = await db.execute(
                select(Organization).where(Organization.id == match.organization_id)
            )
            org = org_result.scalars().first()
            if not org:
                raise HTTPException(status_code=404, detail="Organization not found.")

            grant_result = await db.execute(
                select(Grant).where(Grant.id == match.grant_id)
            )
            grant = grant_result.scalars().first()
            if not grant:
                raise HTTPException(status_code=404, detail="Grant not found.")

            # Build plain dicts before session closes
            org_dict = {
                "name": org.name,
                "mission": org.mission,
                "focus_areas": org.focus_areas or [],
                "location": org.location or "United States",
                "budget_range": org.budget_range or "Not specified",
            }

            grant_dict = {
                "title": grant.title,
                "funder": grant.funder,
                "description": grant.description,
                "deadline": grant.deadline,
                "max_amount": float(grant.max_amount) if grant.max_amount else None,
            }

            match_reasoning_dict = {
                "reasoning": "",
                "alignment_strengths": [],
                "concerns": [],
            }
            if match.match_reasoning:
                try:
                    parsed = _json.loads(match.match_reasoning)
                    if isinstance(parsed, dict):
                        match_reasoning_dict = parsed
                except (_json.JSONDecodeError, TypeError):
                    match_reasoning_dict["reasoning"] = match.match_reasoning

        # ── Groq API call (NO DB session held) ───────────────────────────
        loi_text = await generate_loi(org_dict, grant_dict, match_reasoning_dict)

        # ── Session 2: Save result (short-lived) ────────────────────────
        async with async_session() as db:
            result = await db.execute(
                select(GrantMatch).where(GrantMatch.id == match_id)
            )
            match = result.scalars().first()
            match.generated_loi = loi_text
            await db.commit()

        return {"loi": loi_text}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("LOI generation failed for match %s: %s", match_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"LOI generation failed: {exc}",
        )

