"""
Semantic grant-matching engine powered by Groq (LLaMA 3.3 70B).

Evaluates how well each grant aligns with a nonprofit's mission,
returning structured scores and reasoning for every pair.
"""

import asyncio
import json
import logging
import os
import uuid

from groq import Groq
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.database import async_session
from backend.models import Grant, GrantMatch, Organization

logger = logging.getLogger(__name__)

# ── Groq configuration ──────────────────────────────────────────────────────
client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = "llama-3.3-70b-versatile"
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

# Rate limiting: Groq allows 30 RPM — much faster than Gemini's 5 RPM
INTER_REQUEST_DELAY = 2
RETRY_DELAY = 15
MAX_GRANTS_PER_RUN = 10


# ── Single-pair scoring ─────────────────────────────────────────────────────
async def score_match(org: dict, grant: dict) -> dict | None:
    """
    Ask Groq (LLaMA 3.3 70B) to score how well a grant matches an organization.

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

    async def _call_groq() -> str:
        """Make the Groq API call and return raw text."""
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content.strip()

    try:
        # First attempt
        try:
            raw_text = await _call_groq()
        except Exception as first_exc:
            exc_str = str(first_exc).lower()
            if "429" in exc_str or "resource_exhausted" in exc_str or "rate" in exc_str:
                logger.warning(
                    "Rate limited on '%s' ↔ '%s'. Waiting %ds and retrying...",
                    org.get("name"),
                    grant.get("title"),
                    RETRY_DELAY,
                )
                await asyncio.sleep(RETRY_DELAY)
                raw_text = await _call_groq()  # Retry once
            else:
                raise  # Re-raise non-rate-limit errors

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
            logger.warning("Groq response missing keys: %s", missing)
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


# ── Sequential runner for a single organization ─────────────────────────────
async def run_matching_for_org(
    org_id: str,
    min_score: float = 0.6,
) -> dict:
    """
    Score unmatched grants against the given organization.

    Processes grants sequentially (one at a time) with a delay between
    calls to stay within the Groq rate limit (30 req/min).
    Fetches at most MAX_GRANTS_PER_RUN grants per invocation.

    Uses short-lived DB sessions to avoid Supabase statement timeouts.

    Returns:
        {"processed": int, "matched": int, "skipped": int}
    """
    processed: int = 0
    matched: int = 0
    skipped: int = 0

    # ── Session 1: quick read for org + unmatched grants, then close ─────
    async with async_session() as session:
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
        org_uuid = org_row.id

        already_matched_sub = (
            select(GrantMatch.grant_id)
            .where(GrantMatch.organization_id == org_uuid)
        )
        result = await session.execute(
            select(Grant)
            .where(Grant.is_active == True)  # noqa: E712
            .where(Grant.id.notin_(already_matched_sub))
            .limit(MAX_GRANTS_PER_RUN)
        )
        grants = result.scalars().all()

        # Materialise the data we need so we can close this session
        grant_data = [
            {
                "id": g.id,
                "title": g.title,
                "funder": g.funder,
                "description": g.description,
            }
            for g in grants
        ]
    # Session 1 is now closed

    if not grant_data:
        logger.info("No unmatched grants for org %s.", org_id)
        return {"processed": 0, "matched": 0, "skipped": 0}

    logger.info(
        "Scoring %d unmatched grants for '%s' (max %d per run).",
        len(grant_data),
        org_dict["name"],
        MAX_GRANTS_PER_RUN,
    )

    # ── Process sequentially with rate limiting ──────────────────────────
    for g in grant_data:
        processed = int(processed) + 1

        grant_dict = {
            "title": g["title"],
            "funder": g["funder"],
            "description": g["description"],
        }

        match_result = await score_match(org_dict, grant_dict)

        if match_result is None:
            skipped = int(skipped) + 1
        else:
            score = match_result["match_score"]

            if score < min_score:
                skipped = int(skipped) + 1
            else:
                # ── Session 2: quick insert, then close ──────────────
                reasoning_text = (
                    f"{match_result['reasoning']}\n\n"
                    f"Strengths: {', '.join(match_result['alignment_strengths'])}\n"
                    f"Concerns: {', '.join(match_result['concerns'])}\n"
                    f"Action: {match_result['recommended_action']}"
                )

                async with async_session() as write_session:
                    stmt = (
                        pg_insert(GrantMatch)
                        .values(
                            organization_id=org_uuid,
                            grant_id=g["id"],
                            match_score=score,
                            match_reasoning=reasoning_text,
                            status="new",
                        )
                        .on_conflict_do_nothing(
                            index_elements=["organization_id", "grant_id"],
                        )
                    )
                    await write_session.execute(stmt)
                    await write_session.commit()
                matched = int(matched) + 1

        logger.info(
            "[%d/%d] Scored '%s' — waiting %ds for rate limit...",
            processed,
            len(grant_data),
            g["title"][:50],
            INTER_REQUEST_DELAY,
        )
        await asyncio.sleep(INTER_REQUEST_DELAY)

    summary = {"processed": processed, "matched": matched, "skipped": skipped}
    logger.info("Matching complete for org %s: %s", org_id, summary)
    return summary

