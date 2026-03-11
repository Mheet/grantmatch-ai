"""
Pydantic schemas for request validation and response serialization.
Each entity has a Create schema (input) and an Out schema (output).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ── Organization ─────────────────────────────────────────────────────────────
class OrganizationCreate(BaseModel):
    name: str
    mission: str
    focus_areas: list[str] | None = None
    location: str | None = None
    budget_range: str | None = None
    user_id: str | None = None
    past_funders: list[str] | None = None


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    mission: str
    focus_areas: list[str] | None = None
    location: str | None = None
    budget_range: str | None = None
    user_id: str | None = None
    past_funders: list[str] | None = None
    created_at: datetime


# ── Grant ────────────────────────────────────────────────────────────────────
class GrantCreate(BaseModel):
    title: str
    funder: str
    description: str
    focus_areas: list[str] | None = None
    max_amount: Decimal | None = None
    deadline: datetime | None = None
    source_url: str | None = None
    portal: str | None = None


class GrantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    funder: str
    description: str
    focus_areas: list[str] | None = None
    max_amount: Decimal | None = None
    deadline: datetime | None = None
    source_url: str | None = None
    portal: str | None = None
    scraped_at: datetime
    is_active: bool


# ── Grant Match ──────────────────────────────────────────────────────────────
class GrantMatchCreate(BaseModel):
    organization_id: uuid.UUID
    grant_id: uuid.UUID
    match_score: float | None = None
    match_reasoning: str | None = None
    status: str = "new"


class GrantMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    grant_id: uuid.UUID
    match_score: float | None = None
    match_reasoning: str | None = None
    status: str
    generated_loi: str | None = None
    created_at: datetime


class MatchWithGrantOut(BaseModel):
    """Match record with the full nested Grant object."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    grant_id: uuid.UUID
    match_score: float | None = None
    match_reasoning: str | None = None
    status: str
    generated_loi: str | None = None
    created_at: datetime
    grant: GrantOut


# ── LOI Draft ────────────────────────────────────────────────────────────────
class LOIDraftCreate(BaseModel):
    match_id: uuid.UUID
    content: str
    version: int = 1


class LOIDraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    content: str
    version: int
    created_at: datetime
