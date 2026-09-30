import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def enum_col(e: type[enum.Enum]) -> Enum:
    # native_enum=False: PostgreSQL va SQLite'da bir xil ishlaydi, migratsiya oson
    return Enum(e, native_enum=False, length=24, validate_strings=True)


class Base(DeclarativeBase):
    pass


class IdMixin:
    id: Mapped[int] = mapped_column(primary_key=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class TenantMixin:
    """Har bir biznes jadvalda center_id bo'lishi shart (multi-tenancy)."""

    @declared_attr
    def center_id(cls) -> Mapped[int]:
        return mapped_column(ForeignKey("centers.id", ondelete="CASCADE"), index=True)
