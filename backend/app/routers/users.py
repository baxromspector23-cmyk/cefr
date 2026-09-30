from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_tenant_or_404, require_roles, tenant_select
from ..models import Role, StudentProfile, User
from ..schemas import UserCreate, UserOut
from ..security import hash_password
from ..services.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])

# Kim kimni yarata oladi
CAN_CREATE = {
    Role.center_admin: {Role.teacher, Role.student},
    Role.teacher: {Role.student},
}


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    me: User = Depends(require_roles(Role.center_admin, Role.teacher)),
):
    if body.role not in CAN_CREATE[me.role]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bu rolni yaratishga ruxsat yo'q")
    exists = db.scalar(select(User).where(User.center_id == me.center_id, User.phone == body.phone))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu telefon raqami markazda mavjud")
    user = User(
        center_id=me.center_id,
        role=body.role,
        full_name=body.full_name,
        phone=body.phone,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()
    if user.role == Role.student:
        db.add(StudentProfile(center_id=me.center_id, user_id=user.id))
    log_action(db, me, "user.create", "user", user.id, {"role": user.role.value}, request)
    db.commit()
    return user


@router.get("", response_model=list[UserOut])
def list_users(
    role: Role | None = None,
    db: Session = Depends(get_db),
    me: User = Depends(require_roles(Role.center_admin, Role.teacher)),
):
    stmt = tenant_select(User, me).order_by(User.id)
    if me.role == Role.teacher:  # ustoz faqat o'quvchilarni ko'radi
        stmt = stmt.where(User.role == Role.student)
    if role:
        stmt = stmt.where(User.role == role)
    return db.scalars(stmt).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(require_roles(Role.center_admin, Role.teacher)),
):
    user = get_tenant_or_404(db, User, user_id, me)
    if me.role == Role.teacher and user.role != Role.student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Topilmadi")
    return user
