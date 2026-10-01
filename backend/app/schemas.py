import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import Role


def normalize_phone(v: str) -> str:
    v = re.sub(r"[\s\-()]", "", v or "")
    if not re.fullmatch(r"\+?\d{9,15}", v):
        raise ValueError("Telefon raqami noto'g'ri (masalan +998901234567)")
    return v


class _Phone(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_phone(v)


class LoginIn(_Phone):
    password: str = Field(min_length=1, max_length=128)
    center_slug: str | None = None  # super admin uchun bo'sh


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    center_id: int | None
    role: Role
    full_name: str
    phone: str
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(_Phone):
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.student


class CenterCreate(_Phone):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]{1,58}[a-z0-9]$")
    admin_full_name: str = Field(min_length=2, max_length=160)
    admin_password: str = Field(min_length=8, max_length=128)
    # phone = markaz admini telefoni


class CenterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    is_active: bool


# ---------- Ta'lim & Guruhlar ----------
class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    schedule: str | None = "Du-Chor-Ju 18:00"
    monthly_fee: int = 450000
    teacher_id: int | None = None


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    schedule: str | None
    monthly_fee: int
    teacher_id: int | None
    is_active: bool


class GroupStudentAdd(BaseModel):
    student_id: int


class TestAttemptSync(BaseModel):
    phone: str
    score: int
    total: int
    level: str
    details: dict | None = None


# ---------- Davomat ----------
class SessionCreate(BaseModel):
    group_id: int
    held_on: str | None = None  # YYYY-MM-DD, None bo'lsa bugun


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    teacher_id: int
    held_on: str
    finalized: bool


class QRGenerateOut(BaseModel):
    session_id: int
    token: str
    expires_at: str


class QRScanIn(BaseModel):
    token: str


class AttendanceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    student_id: int
    status: str
    source: str
    marked_at: str


# ---------- Moliya ----------
class PaymentCreate(BaseModel):
    student_id: int
    group_id: int | None = None
    amount: int = Field(gt=0)
    period: str = Field(pattern=r"^\d{4}-\d{2}$")  # "2026-09"
    method: str = "naqd"
    note: str | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    group_id: int | None
    amount: int
    period: str
    method: str | None
    note: str | None
    created_at: str


class FinanceSummaryOut(BaseModel):
    total_revenue: int
    payment_count: int
    period: str

