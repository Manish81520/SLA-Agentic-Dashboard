"""SQLAlchemy models for persisted onboarding datasets."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Base class for database models."""


class Dataset(Base):
    """One uploaded source dataset."""

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    columns: Mapped[list[str]] = mapped_column(JSON_TYPE, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class DatasetMapping(Base):
    """The agent mapping associated with an uploaded dataset."""

    __tablename__ = "dataset_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False, unique=True)
    agent_response: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)


class PartnerRow(Base):
    """One raw partner record in a dataset."""

    __tablename__ = "partner_rows"
    __table_args__ = (
        UniqueConstraint("dataset_id", "identifier_norm", name="uq_partner_rows_dataset_identifier"),
        Index("ix_partner_rows_dataset_position", "dataset_id", "position"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    identifier_norm: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
