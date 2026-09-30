"""Ishlatish (backend papkasida):  python -m scripts.create_super_admin
.env dagi SUPERADMIN_PHONE / SUPERADMIN_PASSWORD / SUPERADMIN_NAME dan foydalanadi."""
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal, engine
from app.models import Base, Role, User
from app.schemas import normalize_phone
from app.security import hash_password


def main() -> None:
    if not settings.superadmin_phone or len(settings.superadmin_password) < 8:
        raise SystemExit(".env da SUPERADMIN_PHONE va kamida 8 belgili SUPERADMIN_PASSWORD kerak")
    Base.metadata.create_all(engine)
    phone = normalize_phone(settings.superadmin_phone)
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.center_id.is_(None), User.phone == phone)):
            print("Super admin allaqachon mavjud")
            return
        db.add(
            User(
                center_id=None,
                role=Role.super_admin,
                full_name=settings.superadmin_name,
                phone=phone,
                password_hash=hash_password(settings.superadmin_password),
            )
        )
        db.commit()
        print("Super admin yaratildi:", phone)


if __name__ == "__main__":
    main()
