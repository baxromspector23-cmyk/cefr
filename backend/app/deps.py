import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Center, Role, User
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Kirish talab qilinadi")
    if creds is None:
        raise unauthorized
    try:
        payload = decode_access_token(creds.credentials)
    except jwt.PyJWTError:
        raise unauthorized
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise unauthorized
    if user.center_id is not None:
        center = db.get(Center, user.center_id)
        if center is None or not center.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Kurs markazi faol emas")
    return user


def require_roles(*roles: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
        return user

    return checker


def tenant_select(model, user: User) -> Select:
    """MULTI-TENANCY: markaz foydalanuvchisi faqat o'z center_id sidagi qatorlarni ko'radi.
    Barcha ro'yxat/qidiruv so'rovlari shu funksiyadan boshlanishi shart."""
    stmt = select(model)
    if user.role == Role.super_admin:
        return stmt
    if user.center_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Markazga biriktirilmagan")
    return stmt.where(model.center_id == user.center_id)


def get_tenant_or_404(db: Session, model, obj_id: int, user: User):
    obj = db.scalar(tenant_select(model, user).where(model.id == obj_id))
    if obj is None:
        # 403 emas, 404: boshqa markaz obyekti mavjudligini ham oshkor qilmaymiz
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topilmadi")
    return obj
