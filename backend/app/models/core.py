import enum
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, IdMixin, TenantMixin, TimestampMixin, enum_col


class Role(str, enum.Enum):
    super_admin = "super_admin"
    center_admin = "center_admin"
    teacher = "teacher"
    student = "student"


class SubStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


class Center(IdMixin, TimestampMixin, Base):
    __tablename__ = "centers"
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Plan(IdMixin, TimestampMixin, Base):
    __tablename__ = "plans"
    name: Mapped[str] = mapped_column(String(80))
    price_monthly: Mapped[int] = mapped_column(Integer)  # so'm, butun son
    price_yearly: Mapped[int] = mapped_column(Integer)
    max_students: Mapped[int] = mapped_column(Integer)


class Subscription(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "subscriptions"
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    status: Mapped[SubStatus] = mapped_column(enum_col(SubStatus), default=SubStatus.active)
    paid_amount: Mapped[int] = mapped_column(Integer, default=0)


class User(IdMixin, TimestampMixin, Base):
    """center_id NULL bo'lsa - platforma super admini."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("center_id", "phone", name="uq_user_center_phone"),)

    center_id: Mapped[int | None] = mapped_column(
        ForeignKey("centers.id", ondelete="CASCADE"), index=True, nullable=True
    )
    role: Mapped[Role] = mapped_column(enum_col(Role))
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(20), index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    telegram_id: Mapped[int | None] = mapped_column(Integer, unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    center: Mapped["Center | None"] = relationship()


class StudentProfile(IdMixin, TimestampMixin, TenantMixin, Base):
    __tablename__ = "student_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    current_level: Mapped[str | None] = mapped_column(String(3))  # A1..C1
    xp: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_on: Mapped[date | None] = mapped_column(Date)
    parent_phone: Mapped[str | None] = mapped_column(String(20))


class RefreshToken(IdMixin, Base):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TelegramLinkCode(IdMixin, Base):
    """Telegram akkauntni bog'lash uchun bir martalik kod."""

    __tablename__ = "telegram_link_codes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(IdMixin, Base):
    __tablename__ = "audit_logs"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    center_id: Mapped[int | None] = mapped_column(ForeignKey("centers.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    data: Mapped[dict | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(45))
