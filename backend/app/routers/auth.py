from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Center, RefreshToken, Role, User
from ..models.base import utcnow
from ..schemas import LoginIn, RefreshIn, TokenOut, UserOut
from ..security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    verify_password,
)
from ..services import ratelimit
from ..services.audit import log_action

router = APIRouter(prefix="/auth", tags=["auth"])

_DUMMY_HASH = hash_password("dummy-password-for-timing")  # foydalanuvchi topilmasa ham vaqt bir xil
BAD = HTTPException(status.HTTP_401_UNAUTHORIZED, "Telefon yoki parol noto'g'ri")


def _as_utc(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _issue(db: Session, user: User) -> TokenOut:
    access = create_access_token(user.id, user.role.value, user.center_id)
    refresh, token_hash, expires = new_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires))
    return TokenOut(access_token=access, refresh_token=refresh, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    key = f"{body.center_slug or '-'}:{body.phone}"
    if ratelimit.is_blocked(key):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Urinishlar ko'p. 15 daqiqadan keyin urining")

    if body.center_slug:
        center = db.scalar(select(Center).where(Center.slug == body.center_slug))
        user = (
            db.scalar(select(User).where(User.center_id == center.id, User.phone == body.phone))
            if center
            else None
        )
    else:  # super admin
        user = db.scalar(
            select(User).where(User.center_id.is_(None), User.phone == body.phone, User.role == Role.super_admin)
        )

    ok = verify_password(body.password, user.password_hash if user else _DUMMY_HASH)
    if not user or not ok or not user.is_active:
        ratelimit.register_fail(key)
        raise BAD

    ratelimit.reset(key)
    user.last_login_at = utcnow()
    tokens = _issue(db, user)
    log_action(db, user, "login", "user", user.id, request=request)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    rt = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(body.refresh_token)))
    if rt is None or rt.revoked_at is not None or _as_utc(rt.expires_at) < utcnow():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessiya tugagan, qayta kiring")
    user = db.get(User, rt.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessiya tugagan, qayta kiring")
    rt.revoked_at = utcnow()  # eski token bir marta ishlaydi (rotation)
    tokens = _issue(db, user)
    db.commit()
    return tokens


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
