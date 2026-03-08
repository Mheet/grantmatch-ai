"""
Database helpers for the scraping pipeline.
Provides upsert logic that gracefully handles duplicate grants.
"""

import logging

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError

from backend.database import async_session
from backend.models import Grant

logger = logging.getLogger(__name__)


async def upsert_grant(grant_data: dict) -> bool:
    """
    Insert a grant into the database.

    Uses PostgreSQL ON CONFLICT DO NOTHING on the unique source_url column
    so repeat scraper runs never crash on duplicates.

    Returns True if a new row was inserted, False if it was skipped.
    """
    async with async_session() as session:
        try:
            stmt = (
                pg_insert(Grant)
                .values(**grant_data)
                .on_conflict_do_nothing(index_elements=["source_url"])
            )
            result = await session.execute(stmt)
            await session.commit()

            inserted = result.rowcount > 0
            if inserted:
                logger.debug("Inserted grant: %s", grant_data.get("title", "?"))
            else:
                logger.debug("Skipped duplicate: %s", grant_data.get("source_url", "?"))
            return inserted

        except SQLAlchemyError as exc:
            await session.rollback()
            logger.error("Failed to upsert grant '%s': %s", grant_data.get("title"), exc)
            return False
