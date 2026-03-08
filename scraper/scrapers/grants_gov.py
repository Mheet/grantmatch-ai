"""
Grants.gov scraper — queries the public search2 REST API (no auth required).
Returns cleaned grant dictionaries ready for DB insertion.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx

logger = logging.getLogger(__name__)

API_URL = "https://api.grants.gov/v1/api/search2"

SEARCH_KEYWORDS: list[str] = [
    "advocacy",
    "community development",
    "social justice",
    "nonprofit",
    "education",
    "health equity",
]

# Maximum results per keyword query (API cap)
ROWS_PER_QUERY = 25


class GrantsGovScraper:
    """Fetches grant opportunities from the Grants.gov search2 API."""

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    # ── Public interface ─────────────────────────────────────────────────
    async def scrape(self) -> list[dict]:
        """
        Search Grants.gov for each keyword and return de-duplicated,
        cleaned grant records.
        """
        seen_ids: set[str] = set()
        grants: list[dict] = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for keyword in SEARCH_KEYWORDS:
                results = await self._search(client, keyword)
                for opp in results:
                    opp_id = str(opp.get("id", opp.get("opportunityId", "")))
                    if not opp_id or opp_id in seen_ids:
                        continue
                    seen_ids.add(opp_id)

                    cleaned = self._clean(opp, opp_id)
                    if cleaned:
                        grants.append(cleaned)

        logger.info(
            "Grants.gov scrape complete — %d unique opportunities found.", len(grants)
        )
        return grants

    # ── Private helpers ──────────────────────────────────────────────────
    async def _search(self, client: httpx.AsyncClient, keyword: str) -> list[dict]:
        """Execute a single keyword search against the API."""
        payload = {
            "keyword": keyword,
            "oppStatuses": "posted|forecasted",
            "rows": ROWS_PER_QUERY,
        }
        try:
            response = await client.post(
                API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            # The API nests results under different keys depending on version
            opportunities = (
                data.get("oppHits")
                or data.get("opportunities")
                or data.get("data", {}).get("oppHits", [])
            )
            if not isinstance(opportunities, list):
                opportunities = []

            logger.info(
                "Keyword '%s' returned %d results.", keyword, len(opportunities)
            )
            return opportunities

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Grants.gov API HTTP %s for keyword '%s': %s",
                exc.response.status_code,
                keyword,
                exc,
            )
            return []
        except httpx.RequestError as exc:
            logger.warning(
                "Grants.gov API request failed for keyword '%s': %s", keyword, exc
            )
            return []

    def _clean(self, opp: dict, opp_id: str) -> dict | None:
        """
        Normalise a raw API opportunity into a dict matching the
        grants table columns.
        """
        title = (
            opp.get("title")
            or opp.get("oppTitle")
            or opp.get("opportunityTitle")
            or ""
        ).strip()
        funder = (
            opp.get("agency")
            or opp.get("agencyCode")
            or opp.get("agencyName")
            or "Unknown"
        ).strip()
        description = (
            opp.get("synopsis")
            or opp.get("description")
            or opp.get("synopsisDesc")
            or ""
        ).strip()

        if not title:
            return None

        # ── Deadline ─────────────────────────────────────────────────
        deadline = self._parse_date(
            opp.get("closeDate")
            or opp.get("closeDateStr")
            or opp.get("applicationsDueDate")
        )

        # ── Max award amount ─────────────────────────────────────────
        max_amount = self._parse_amount(
            opp.get("awardCeiling")
            or opp.get("maxAwardAmount")
        )

        # ── Focus areas from category keywords ──────────────────────
        focus_areas: list[str] = []
        raw_cats = (
            opp.get("fundingCategories")
            or opp.get("categoryOfFundingActivity")
            or ""
        )
        if isinstance(raw_cats, str) and raw_cats:
            focus_areas = [c.strip() for c in raw_cats.split("|") if c.strip()]
        elif isinstance(raw_cats, list):
            focus_areas = raw_cats

        source_url = f"https://grants.gov/search-results-detail/{opp_id}"

        return {
            "title": title,
            "funder": funder,
            "description": description or "No description available.",
            "focus_areas": focus_areas or None,
            "max_amount": max_amount,
            "deadline": deadline,
            "source_url": source_url,
            "portal": "grants.gov",
            "scraped_at": datetime.now(timezone.utc),
            "is_active": True,
        }

    # ── Parsing utilities ────────────────────────────────────────────────
    @staticmethod
    def _parse_date(raw: str | None) -> datetime | None:
        """Try common Grants.gov date formats."""
        if not raw:
            return None
        for fmt in ("%m/%d/%Y", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
        return None

    @staticmethod
    def _parse_amount(raw) -> Decimal | None:
        """Safely convert a ceiling value to Decimal."""
        if raw is None:
            return None
        try:
            value = Decimal(str(raw))
            return value if value > 0 else None
        except (InvalidOperation, ValueError):
            return None
