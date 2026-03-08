"""
Semantic grant-matching engine powered by Google Gemini.

Evaluates how well each grant aligns with a nonprofit's mission,
returning structured scores and reasoning for every pair.
"""

import asyncio
import json
import logging
import os
import uuid

from google import genai
from google.genai import types
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.database import async_session
from backend.models import Grant, GrantMatch, Organization

logger = logging.getLogger(__name__)

# ── Gemini configuration ─────────────────────────────────────────────────────
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-2.5-flash"
# ── Prompt template ──────────────────────────────────────────────────────────
MATCH_PROMPT = """\
You are an expert nonprofit grants consultant with 20+ years of experience \
matching advocacy organizations to funding opportunities.

Evaluate how well the following grant aligns with the organization's mission \
and focus areas. Consider programmatic fit, funder alignment, geographic \
relevance, and capacity requirements.

ORGANIZATION:
- Name: {org_name}
- Mission: {org_mission}
- Focus Areas: {org_focus_areas}

GRANT OPPORTUNITY:
- Title: {grant_title}
- Funder: {grant_funder}
- Description: {grant_description}

Return ONLY valid raw JSON with absolutely no markdown formatting, no code \
fences, no conversational text — just the raw JSON object and nothing else.

The JSON object must have exactly these keys:
{{
  "match_score": <float between 0.0 and 1.0>,
  "reasoning": "<2-3 sentence explanation of why this score was given>",
  "alignment_strengths": ["<strength 1>", "<strength 2>", ...],
  "concerns": ["<concern 1>", "<concern 2>", ...],
  "recommended_action": "<one of: apply, research_more, skip>"
}}
"""

# Maximum concurrent API calls per batch
BATCH_SIZE = 5


# ── Single-pair scoring ─────────────────────────────────────────────────────
async def score_match(org: dict, grant: dict) -> dict | None:
    """
    Ask Gemini to score how well a grant matches an organization.

    Returns a validated dict with match_score, reasoning,
    alignment_strengths, concerns, and recommended_action.
    Returns None if the API call or parsing fails.
    """
    prompt = MATCH_PROMPT.format(
        org_name=org.get("name", "Unknown"),
        org_mission=org.get("mission", ""),
        org_focus_areas=", ".join(org.get("focus_areas") or ["General"]),
        grant_title=grant.get("title", "Unknown"),
        grant_funder=grant.get("funder", "Unknown"),
        grant_description=grant.get("description", "")[:2000],
    )

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        raw_text = response.text.strip()

        data = json.loads(raw_text)

        # ── Validate required keys & types ───────────────────────────
        REQUIRED_KEYS = {
            "match_score",
            "reasoning",
            "alignment_strengths",
            "concerns",
            "recommended_action",
        }
        if not REQUIRED_KEYS.issubset(data.keys()):
            missing = REQUIRED_KEYS - data.keys()
            logger.warning("Gemini response missing keys: %s", missing)
            return None

        # Clamp score to [0, 1]
        data["match_score"] = max(0.0, min(1.0, float(data["match_score"])))

        # Validate recommended_action
        valid_actions = {"apply", "research_more", "skip"}
        if data["recommended_action"] not in valid_actions:
            data["recommended_action"] = "research_more"

        return data

    except Exception as exc:
        logger.error(
            "Error scoring '%s' ↔ '%s': %s",
            org.get("name"),
            grant.get("title"),
            exc,
        )
        return None


# ── Batch runner for a single organization ───────────────────────────────────
async def run_matching_for_org(
    org_id: str,
    min_score: float = 0.4,
) -> dict:
    """
    Score every unmatched grant against the given organization.

    Processes grants in batches of BATCH_SIZE using asyncio.gather.
    Saves qualifying matches (>= min_score) to the grant_matches table.

    Returns:
        {"processed": int, "matched": int, "skipped": int}
    """
    processed = 0
    matched = 0
    skipped = 0

    async with async_session() as session:
        # ── Fetch organization ───────────────────────────────────────
        result = await session.execute(
            select(Organization).where(Organization.id == uuid.UUID(org_id))
        )
        org_row = result.scalars().first()
        if not org_row:
            logger.error("Organization %s not found.", org_id)
            return {"processed": 0, "matched": 0, "skipped": 0}

        org_dict = {
            "name": org_row.name,
            "mission": org_row.mission,
            "focus_areas": org_row.focus_areas or [],
        }

        # ── Fetch grants NOT yet matched to this org ─────────────────
        already_matched_sub = (
            select(GrantMatch.grant_id)
            .where(GrantMatch.organization_id == org_row.id)
        )
        result = await session.execute(
            select(Grant)
            .where(Grant.is_active == True)  # noqa: E712
            .where(Grant.id.notin_(already_matched_sub))
        )
        grants = result.scalars().all()

        if not grants:
            logger.info("No unmatched grants for org %s.", org_id)
            return {"processed": 0, "matched": 0, "skipped": 0}

        logger.info(
            "Scoring %d unmatched grants for '%s'.", len(grants), org_row.name
        )

        # ── Process in batches ───────────────────────────────────────
        for i in range(0, len(grants), BATCH_SIZE):
            batch = grants[i : i + BATCH_SIZE]

            grant_dicts = [
                {
                    "title": g.title,
                    "funder": g.funder,
                    "description": g.description,
                }
                for g in batch
            ]

            results = await asyncio.gather(
                *[score_match(org_dict, gd) for gd in grant_dicts],
                return_exceptions=True,
            )

            for grant_obj, match_result in zip(batch, results):
                processed += 1

                if isinstance(match_result, Exception):
                    logger.error(
                        "Exception scoring grant %s: %s",
                        grant_obj.id,
                        match_result,
                    )
                    skipped += 1
                    continue

                if match_result is None:
                    skipped += 1
                    continue

                score = match_result["match_score"]

                if score < min_score:
                    skipped += 1
                    continue

                # ── Persist the match ────────────────────────────────
                reasoning_text = (
                    f"{match_result['reasoning']}\n\n"
                    f"Strengths: {', '.join(match_result['alignment_strengths'])}\n"
                    f"Concerns: {', '.join(match_result['concerns'])}\n"
                    f"Action: {match_result['recommended_action']}"
                )

                stmt = (
                    pg_insert(GrantMatch)
                    .values(
                        organization_id=org_row.id,
                        grant_id=grant_obj.id,
                        match_score=score,
                        match_reasoning=reasoning_text,
                        status="new",
                    )
                    .on_conflict_do_nothing(
                        constraint="uq_org_grant",
                    )
                )
                await session.execute(stmt)
                matched += 1

        await session.commit()

    summary = {"processed": processed, "matched": matched, "skipped": skipped}
    logger.info("Matching complete for org %s: %s", org_id, summary)
    return summary
