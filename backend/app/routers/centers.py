from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_roles
from ..models import Center, Role, User
from ..schemas import CenterCreate, CenterOut, UserOut
from ..security import hash_password
from ..services.audit import log_action

router = APIRouter(prefix="/centers", tags=["super-admin"])


@router.post("", response_model=dict, status_code=201)
def create_center(
    body: CenterCreate,
    request: Request,
    db: Session = Depends(get_db),
    me: User = Depends(require_roles(Role.super_admin)),
):
    if db.scalar(select(Center).where(Center.slug == body.slug)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu slug band")
    center = Center(name=body.name, slug=body.slug, phone=body.phone)
    db.add(center)
    db.flush()
    admin = User(
        center_id=center.id,
        role=Role.center_admin,
        full_name=body.admin_full_name,
        phone=body.phone,
        password_hash=hash_password(body.admin_password),
    )
    db.add(admin)
    db.flush()
    log_action(db, me, "center.create", "center", center.id, {"slug": center.slug}, request, center_id=center.id)
    db.commit()
    return {
        "center": CenterOut.model_validate(center).model_dump(),
        "admin": UserOut.model_validate(admin).model_dump(mode="json"),
    }


@router.get("", response_model=list[CenterOut])
def list_centers(db: Session = Depends(get_db), me: User = Depends(require_roles(Role.super_admin))):
    return db.scalars(select(Center).order_by(Center.id)).all()


@router.patch("/{center_id}/active", response_model=CenterOut)
def set_active(
    center_id: int,
    active: bool,
    request: Request,
    db: Session = Depends(get_db),
    me: User = Depends(require_roles(Role.super_admin)),
):
    center = db.get(Center, center_id)
    if center is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topilmadi")
    center.is_active = active
    log_action(db, me, "center.set_active", "center", center.id, {"active": active}, request, center_id=center.id)
    db.commit()
    return center
