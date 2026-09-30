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
