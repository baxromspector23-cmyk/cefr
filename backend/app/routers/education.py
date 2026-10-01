from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_tenant_or_404, require_roles, tenant_select
from ..models import Group, GroupStudent, Role, StudentProfile, User
from ..schemas import GroupCreate, GroupOut, GroupStudentAdd, TestAttemptSync
from ..services.audit import log_action

router = APIRouter(prefix="/education", tags=["education"])


@router.get("/groups", response_model=list[GroupOut])
def list_groups(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = tenant_select(Group, user).order_by(Group.name)
    return db.scalars(stmt).all()


@router.post("/groups", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate,
    user: User = Depends(require_roles(Role.super_admin, Role.center_admin)),
    db: Session = Depends(get_db),
):
    if user.center_id is None and user.role != Role.super_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Markazga biriktirilmagan")

    center_id = user.center_id
    if center_id is None and user.role == Role.super_admin:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Super admin guruh yaratishda markaz ko'rsatishi shart")

    group = Group(
        center_id=center_id,
        name=payload.name,
        schedule=payload.schedule,
        monthly_fee=payload.monthly_fee,
        teacher_id=payload.teacher_id,
    )
    db.add(group)
    db.commit()
    log_action(db, user, "create_group", "group", group.id)
    db.commit()
    return group


@router.get("/groups/{group_id}/students")
def list_group_students(
    group_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_tenant_or_404(db, Group, group_id, user)
    stmt = (
        select(User, GroupStudent.joined_on)
        .join(GroupStudent, GroupStudent.student_id == User.id)
        .where(GroupStudent.group_id == group.id, GroupStudent.left_on.is_(None))
    )
    rows = db.execute(stmt).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "phone": u.phone,
            "joined_on": str(joined_on),
        }
        for u, joined_on in rows
    ]


@router.post("/groups/{group_id}/students", status_code=status.HTTP_201_CREATED)
def add_student_to_group(
    group_id: int,
    payload: GroupStudentAdd,
    user: User = Depends(require_roles(Role.super_admin, Role.center_admin, Role.teacher)),
    db: Session = Depends(get_db),
):
    group = get_tenant_or_404(db, Group, group_id, user)
    student = get_tenant_or_404(db, User, payload.student_id, user)
    if student.role != Role.student:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Faqat o'quvchi rolidagi foydalanuvchini qo'shish mumkin")

    existing = db.scalar(
        select(GroupStudent).where(
            GroupStudent.group_id == group.id,
            GroupStudent.student_id == student.id,
            GroupStudent.left_on.is_(None),
        )
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "O'quvchi allaqachon ushbu guruhda")

    rel = GroupStudent(
        center_id=group.center_id,
        group_id=group.id,
        student_id=student.id,
        joined_on=date.today(),
    )
    db.add(rel)
    db.commit()
    return {"status": "ok", "message": f"{student.full_name} guruhga qo'shildi"}


@router.post("/tests/sync-attempt")
def sync_test_attempt(
    payload: TestAttemptSync,
    db: Session = Depends(get_db),
):
    """Telegram Bot yoki Web App dan CEFR test natijalarini sinxronlash."""
    phone = payload.phone.strip()
    user = db.scalar(select(User).where(User.phone == phone))
    if user:
        profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
        if profile:
            profile.current_level = payload.level
        else:
            db.add(StudentProfile(user_id=user.id, current_level=payload.level))
        db.commit()

    return {
        "status": "ok",
        "phone": phone,
        "level": payload.level,
        "score": payload.score,
        "total": payload.total,
        "message": "Natija muvaffaqiyatli sinxronlandi",
    }
