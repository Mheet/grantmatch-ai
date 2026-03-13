"""
Master scraping pipeline — orchestrates all scrapers concurrently,
normalises text, and upserts results into the database.
"""

import asyncio
import html
import logging
import re

from scraper.db import upsert_grant
from scraper.scrapers.grants_gov import GrantsGovScraper
from scraper.scrapers.foundation_scraper import RWJFScraper

logger = logging.getLogger(__name__)


# ── Text normalization ───────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    """
    Strip HTML tags, unescape HTML entities (e.g. &amp; → &),
    and collapse whitespace into single spaces.
    Uses only Python built-ins (re, html).
    """
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)       # strip HTML tags
    text = re.sub(r"\s+", " ", text).strip()   # normalise whitespace
    return text


class ScrapePipeline:
    """Runs all scrapers concurrently and upserts cleaned results."""

    async def run(self) -> dict:
        """
        Execute every registered scraper in parallel, clean descriptions,
        and upsert into the grants table.

        Returns:
            {"scraped": int, "saved": int, "errors": int}
        """
        scraped: int = 0
        saved: int = 0
        errors: int = 0

        # ── Run scrapers concurrently ────────────────────────────────
        grants_gov = GrantsGovScraper()
        rwjf = RWJFScraper()

        results = await asyncio.gather(
            grants_gov.scrape(),
            rwjf.scrape(),
            return_exceptions=True,
        )

        all_grants: list[dict] = []

        for i, result in enumerate(results):
            scraper_name = ["GrantsGov", "RWJF"][i]
            if isinstance(result, Exception):
                logger.error(
                    "%s scraper raised an exception: %s", scraper_name, result
                )
                errors = int(errors) + 1
                continue
            if isinstance(result, list):
                logger.info(
                    "%s scraper returned %d grants.", scraper_name, len(result)
                )
                all_grants.extend(result)
            else:
                logger.warning(
                    "%s scraper returned unexpected type: %s",
                    scraper_name,
                    type(result).__name__,
                )

        scraped = len(all_grants)

        # ── Clean & upsert ───────────────────────────────────────────
        for grant in all_grants:
            try:
                grant["description"] = clean_text(grant.get("description", ""))
                grant["title"] = clean_text(grant.get("title", ""))

                inserted = await upsert_grant(grant)
                if inserted:
                    saved = int(saved) + 1
            except Exception as exc:
                logger.error("Error upserting grant '%s': %s", grant.get("title"), exc)
                errors = int(errors) + 1

        summary = {"scraped": scraped, "saved": saved, "errors": errors}
        logger.info("Pipeline complete: %s", summary)
        return summary
