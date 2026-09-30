import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TenantMixin, enum_col


class AttStatus(str, enum.Enum):
    present = "present"        # keldi
    absent = "absent"          # kelmadi
    late = "late"              # kechikdi
    excused = "excused"        # sababli
    unexcused = "unexcused"    # sababsiz


class AttSource(str, enum.Enum):
    teacher = "teacher"
    telegram = "telegram"
    qr = "qr"


class ClassSession(IdMixin, TenantMixin, Base):
    """Guruhning bitta dars kuni."""

    __tablename__ = "class_sessions"
    __table_args__ = (UniqueConstraint("group_id", "held_on", name="uq_session_day"),)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    held_on: Mapped[date] = mapped_column(Date)
    finalized: Mapped[bool] = mapped_column(Boolean, default=False)  # ustoz yakuniy tasdiqlagan


class AttendanceRecord(IdMixin, TenantMixin, Base):
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="uq_attendance"),)
    session_id: Mapped[int] = mapped_column(ForeignKey("class_sessions.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[AttStatus] = mapped_column(enum_col(AttStatus))
    source: Mapped[AttSource] = mapped_column(enum_col(AttSource))
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confirmed_by_teacher: Mapped[bool] = mapped_column(Boolean, default=False)


class AttendanceQrToken(IdMixin, TenantMixin, Base):
    """Qisqa muddatli (30-60 soniya) QR token."""

    __tablename__ = "attendance_qr_tokens"
    session_id: Mapped[int] = mapped_column(ForeignKey("class_sessions.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
