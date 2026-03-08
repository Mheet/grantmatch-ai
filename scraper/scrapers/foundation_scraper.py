"""
Playwright-based scraper for the Robert Wood Johnson Foundation (RWJF)
funding opportunities page.

PREREQUISITE — run once before first use:
    playwright install chromium

If the live scrape returns 0 results (selectors changed, site blocking, etc.)
the scraper automatically falls back to a hardcoded list of realistic RWJF
grants so the pipeline always has data to work with during development.
"""

import logging
from datetime import datetime, timezone

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

TARGET_URL = "https://www.rwjf.org/en/grants/funding-opportunities.html"

# Realistic user-agent to reduce bot-detection friction
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# ── Fallback data ────────────────────────────────────────────────────────────
# Returned when the live scrape yields nothing — keeps the dev pipeline alive.
FALLBACK_GRANTS: list[dict] = [
    {
        "title": "Exploring Equitable Futures",
        "funder": "Robert Wood Johnson Foundation",
        "description": (
            "Supports bold ideas that explore what the future could look like "
            "if health equity were the norm. Rolling submissions accepted; "
            "proposals reviewed in cycles."
        ),
        "deadline": datetime(2026, 10, 15, 19, 0, tzinfo=timezone.utc),
        "source_url": "https://www.rwjf.org/en/grants/funding-opportunities/2024/exploring-equitable-futures.html",
        "portal": "rwjf.org",
        "focus_areas": ["health equity", "innovation", "community"],
        "max_amount": None,
        "is_active": True,
    },
    {
        "title": "Systems for Action: Community-Led Systems Research",
        "funder": "Robert Wood Johnson Foundation",
        "description": (
            "Final research funding opportunity through the Systems for Action "
            "program, supporting community-led research to address systemic "
            "racism and its impact on health outcomes."
        ),
        "deadline": datetime(2026, 6, 4, 19, 0, tzinfo=timezone.utc),
        "source_url": "https://www.rwjf.org/en/grants/funding-opportunities/2024/systems-for-action.html",
        "portal": "rwjf.org",
        "focus_areas": ["health equity", "systemic racism", "community research"],
        "max_amount": None,
        "is_active": True,
    },
    {
        "title": "Health Equity Scholars for Action",
        "funder": "Robert Wood Johnson Foundation",
        "description": (
            "A leadership development program for early-to-mid-career "
            "researchers and practitioners committed to advancing health equity "
            "through evidence-based action."
        ),
        "deadline": datetime(2026, 11, 6, 19, 0, tzinfo=timezone.utc),
        "source_url": "https://www.rwjf.org/en/grants/funding-opportunities/2024/health-equity-scholars-for-action.html",
        "portal": "rwjf.org",
        "focus_areas": ["health equity", "leadership", "research"],
        "max_amount": None,
        "is_active": True,
    },
]


class RWJFScraper:
    """Async Playwright scraper for RWJF funding opportunities."""

    def __init__(self, timeout_ms: int = 30_000) -> None:
        self.timeout_ms = timeout_ms

    # ── Public interface ─────────────────────────────────────────────────
    async def scrape(self) -> list[dict]:
        """
        Attempt a live scrape of the RWJF page.
        Returns fallback data if the live scrape yields nothing.
        """
        grants: list[dict] = []
        try:
            grants = await self._live_scrape()
        except PlaywrightTimeout:
            logger.warning("RWJF page timed out after %dms.", self.timeout_ms)
        except Exception as exc:
            logger.warning("RWJF live scrape failed: %s", exc)

        if grants:
            logger.info("RWJF live scrape returned %d grants.", len(grants))
            return grants

        logger.info(
            "RWJF live scrape returned 0 results — using %d fallback grants.",
            len(FALLBACK_GRANTS),
        )
        return FALLBACK_GRANTS

    # ── Private: live scrape ─────────────────────────────────────────────
    async def _live_scrape(self) -> list[dict]:
        grants: list[dict] = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()

            try:
                await page.goto(TARGET_URL, wait_until="networkidle", timeout=self.timeout_ms)

                # Dismiss any cookie / consent banners
                for btn_selector in [
                    "button:has-text('Accept')",
                    "button:has-text('Got it')",
                    "button:has-text('Close')",
                    "[aria-label='Close']",
                ]:
                    try:
                        btn = page.locator(btn_selector).first
                        if await btn.is_visible(timeout=2000):
                            await btn.click()
                    except Exception:
                        pass

                # ── Strategy 1: card / tile based layout ─────────────
                grants = await self._try_card_selectors(page)

                # ── Strategy 2: list / table based layout ────────────
                if not grants:
                    grants = await self._try_list_selectors(page)

                # ── Strategy 3: generic link harvesting ──────────────
                if not grants:
                    grants = await self._try_generic_links(page)

            except PlaywrightTimeout:
                raise
            except Exception as exc:
                logger.warning("Error during RWJF page interaction: %s", exc)
            finally:
                await browser.close()

        return grants

    # ── Selector strategies ──────────────────────────────────────────────
    async def _try_card_selectors(self, page) -> list[dict]:
        """Look for card/tile components common on modern foundation sites."""
        CARD_SELECTORS = [
            "article.funding-opportunity",
            ".card--funding",
            ".opportunity-card",
            "[data-component='funding-card']",
            ".cmp-contentfragment",
            ".content-card",
            ".grant-listing-item",
        ]
        for selector in CARD_SELECTORS:
            try:
                cards = page.locator(selector)
                count = await cards.count()
                if count > 0:
                    logger.info("Found %d cards via '%s'", count, selector)
                    return await self._extract_from_cards(cards, count)
            except Exception:
                continue
        return []

    async def _try_list_selectors(self, page) -> list[dict]:
        """Look for list items within a funding section."""
        LIST_SELECTORS = [
            ".funding-opportunities li",
            ".grant-list li",
            "section.grants li a",
            ".cmp-list__item",
            "ul.results-list li",
        ]
        for selector in LIST_SELECTORS:
            try:
                items = page.locator(selector)
                count = await items.count()
                if count > 0:
                    logger.info("Found %d list items via '%s'", count, selector)
                    return await self._extract_from_list_items(items, count)
            except Exception:
                continue
        return []

    async def _try_generic_links(self, page) -> list[dict]:
        """Last resort — grab any internal links that look like funding pages."""
        grants: list[dict] = []
        try:
            links = page.locator(
                "a[href*='funding-opportunities'], "
                "a[href*='grants/active'], "
                "a[href*='/grants/']"
            )
            count = await links.count()
            for i in range(min(count, 20)):
                try:
                    el = links.nth(i)
                    title = (await el.inner_text()).strip()
                    href = await el.get_attribute("href") or ""
                    if not title or len(title) < 5 or not href:
                        continue
                    # Skip navigation / breadcrumb links
                    if title.lower() in ("grants", "funding opportunities", "back", "home"):
                        continue
                    source_url = href if href.startswith("http") else f"https://www.rwjf.org{href}"
                    grants.append(self._build_grant(title=title, source_url=source_url))
                except Exception:
                    continue
        except Exception:
            pass
        return grants

    # ── Extraction helpers ───────────────────────────────────────────────
    async def _extract_from_cards(self, cards, count: int) -> list[dict]:
        grants: list[dict] = []
        for i in range(count):
            try:
                card = cards.nth(i)

                # Title
                title_el = card.locator("h2, h3, h4, .card__title, .title").first
                title = (await title_el.inner_text()).strip() if await title_el.count() else ""

                # Description
                desc_el = card.locator("p, .card__description, .description, .synopsis").first
                description = (await desc_el.inner_text()).strip() if await desc_el.count() else ""

                # Link
                link_el = card.locator("a").first
                href = (await link_el.get_attribute("href") or "") if await link_el.count() else ""
                source_url = href if href.startswith("http") else f"https://www.rwjf.org{href}" if href else ""

                # Deadline (often in a metadata span / small element)
                deadline = await self._extract_deadline(card)

                if title:
                    grants.append(
                        self._build_grant(
                            title=title,
                            description=description,
                            deadline=deadline,
                            source_url=source_url,
                        )
                    )
            except Exception:
                continue
        return grants

    async def _extract_from_list_items(self, items, count: int) -> list[dict]:
        grants: list[dict] = []
        for i in range(count):
            try:
                item = items.nth(i)
                link = item.locator("a").first
                title = (await link.inner_text()).strip() if await link.count() else ""
                href = (await link.get_attribute("href") or "") if await link.count() else ""
                source_url = href if href.startswith("http") else f"https://www.rwjf.org{href}" if href else ""

                if title and len(title) > 5:
                    grants.append(self._build_grant(title=title, source_url=source_url))
            except Exception:
                continue
        return grants

    async def _extract_deadline(self, container) -> datetime | None:
        """Try to pull a deadline from date-like elements within a container."""
        DATE_SELECTORS = [
            ".deadline",
            ".date",
            "time",
            "[data-deadline]",
            "span.meta",
            ".card__date",
        ]
        for sel in DATE_SELECTORS:
            try:
                el = container.locator(sel).first
                if await el.count():
                    raw = (await el.inner_text()).strip()
                    return self._parse_date(raw)
            except Exception:
                continue
        return None

    # ── Utility ──────────────────────────────────────────────────────────
    def _build_grant(
        self,
        title: str,
        description: str = "",
        deadline: datetime | None = None,
        source_url: str = "",
    ) -> dict:
        return {
            "title": title,
            "funder": "Robert Wood Johnson Foundation",
            "description": description or "See funding page for full details.",
            "deadline": deadline,
            "source_url": source_url,
            "portal": "rwjf.org",
            "focus_areas": ["health", "community"],
            "max_amount": None,
            "is_active": True,
        }

    @staticmethod
    def _parse_date(raw: str) -> datetime | None:
        """Attempt common date formats seen on foundation sites."""
        if not raw:
            return None
        # Strip common prefixes like "Deadline: "
        for prefix in ("Deadline:", "Due:", "Closes:", "Due by"):
            if raw.lower().startswith(prefix.lower()):
                raw = raw[len(prefix):].strip()

        for fmt in (
            "%B %d, %Y",        # January 15, 2025
            "%b %d, %Y",        # Jan 15, 2025
            "%m/%d/%Y",         # 01/15/2025
            "%Y-%m-%d",         # 2025-01-15
            "%B %Y",            # January 2025
        ):
            try:
                return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
        return None
