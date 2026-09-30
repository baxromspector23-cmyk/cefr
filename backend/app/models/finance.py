import enum
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, IdMixin, TenantMixin, enum_col, utcnow


class PaymentKind(str, enum.Enum):
    payment = "payment"        # o'quvchi to'lovi
    adjustment = "adjustment"  # tuzatish (manfiy ham bo'lishi mumkin)


class PayRuleKind(str, enum.Enum):
    fixed_monthly = "fixed_monthly"      # oylik maosh
    per_student = "per_student"          # o'quvchi boshiga
    percent = "percent"                  # guruh tushumidan foiz
    per_lesson = "per_lesson"            # dars soatiga


class Payment(IdMixin, TenantMixin, Base):
    """LEDGER: yozuv o'chirilmaydi va tahrirlanmaydi. Xato bo'lsa - adjustment qo'shiladi.
    Pul so'mda, BUTUN son (float ishlatilmaydi)."""

    __tablename__ = "payments"
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"))
    kind: Mapped[PaymentKind] = mapped_column(enum_col(PaymentKind), default=PaymentKind.payment)
    amount: Mapped[int] = mapped_column(Integer)
    period: Mapped[str] = mapped_column(String(7), index=True)  # "2026-09"
    method: Mapped[str | None] = mapped_column(String(30))       # naqd/karta/click/payme
    note: Mapped[str | None] = mapped_column(String(255))
    reverses_id: Mapped[int | None] = mapped_column(ForeignKey("payments.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TeacherPayRule(IdMixin, TenantMixin, Base):
    __tablename__ = "teacher_pay_rules"
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[PayRuleKind] = mapped_column(enum_col(PayRuleKind))
    amount: Mapped[int] = mapped_column(Integer)  # so'm; percent uchun: 3000 = 30.00% (bazis punkt)
    effective_from: Mapped[date] = mapped_column(Date)


class TeacherAccrual(IdMixin, TenantMixin, Base):
    """Oy oxirida hisoblangan maosh (qanday hisoblangani details'da)."""

    __tablename__ = "teacher_accruals"
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TeacherPayout(IdMixin, TenantMixin, Base):
    """Ustozga haqiqatan berilgan pul - alohida yozuv."""

    __tablename__ = "teacher_payouts"
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    period: Mapped[str] = mapped_column(String(7))
    amount: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
