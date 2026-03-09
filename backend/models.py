"""
SQLAlchemy declarative models — mirrors the Supabase SQL schema exactly.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all models."""
    pass


# ── Organizations ────────────────────────────────────────────────────────────
class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    mission: Mapped[str] = mapped_column(Text, nullable=False)
    focus_areas = mapped_column(ARRAY(Text), nullable=True)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget_range: Mapped[str | None] = mapped_column(Text, nullable=True)
    past_funders = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    matches: Mapped[list["GrantMatch"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization {self.name!r}>"


# ── Grants ───────────────────────────────────────────────────────────────────
class Grant(Base):
    __tablename__ = "grants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    funder: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    focus_areas = mapped_column(ARRAY(Text), nullable=True)
    max_amount = mapped_column(Numeric, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_url: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
    portal: Mapped[str | None] = mapped_column(Text, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    matches: Mapped[list["GrantMatch"]] = relationship(
        back_populates="grant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Grant {self.title!r}>"


# ── Grant Matches ────────────────────────────────────────────────────────────
class GrantMatch(Base):
    __tablename__ = "grant_matches"
    __table_args__ = (
        UniqueConstraint("organization_id", "grant_id", name="uq_org_grant"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False
    )
    grant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grants.id"), nullable=False
    )
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="new")
    generated_loi: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="matches")
    grant: Mapped["Grant"] = relationship(back_populates="matches")
    loi_drafts: Mapped[list["LOIDraft"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GrantMatch org={self.organization_id} grant={self.grant_id} score={self.match_score}>"


# ── LOI Drafts ───────────────────────────────────────────────────────────────
class LOIDraft(Base):
    __tablename__ = "loi_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grant_matches.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    match: Mapped["GrantMatch"] = relationship(back_populates="loi_drafts")

    def __repr__(self) -> str:
        return f"<LOIDraft match={self.match_id} v{self.version}>"
