import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_tenant_or_404, require_roles, tenant_select
from ..models import (
    AttSource,
    AttendanceQrToken,
    AttendanceRecord,
    AttStatus,
    ClassSession,
    Group,
    Role,
    User,
)
from ..schemas import AttendanceRecordOut, QRGenerateOut, QRScanIn, SessionCreate, SessionOut

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    user: User = Depends(require_roles(Role.super_admin, Role.center_admin, Role.teacher)),
    db: Session = Depends(get_db),
):
    group = get_tenant_or_404(db, Group, payload.group_id, user)
    held_date = (
        datetime.strptime(payload.held_on, "%Y-%m-%d").date()
        if payload.held_on
        else date.today()
    )

    existing = db.scalar(
        select(ClassSession).where(
            ClassSession.group_id == group.id,
            ClassSession.held_on == held_date,
        )
    )
    if existing:
        return SessionOut(
            id=existing.id,
            group_id=existing.group_id,
            teacher_id=existing.teacher_id,
            held_on=str(existing.held_on),
            finalized=existing.finalized,
        )

    session = ClassSession(
        center_id=group.center_id,
        group_id=group.id,
        teacher_id=user.id,
        held_on=held_date,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionOut(
        id=session.id,
        group_id=session.group_id,
        teacher_id=session.teacher_id,
        held_on=str(session.held_on),
        finalized=session.finalized,
    )


@router.post("/sessions/{session_id}/generate-qr", response_model=QRGenerateOut)
def generate_qr_token(
    session_id: int,
    user: User = Depends(require_roles(Role.super_admin, Role.center_admin, Role.teacher)),
    db: Session = Depends(get_db),
):
    session = get_tenant_or_404(db, ClassSession, session_id, user)
    token_str = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token_str.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    qr = AttendanceQrToken(
        center_id=session.center_id,
        session_id=session.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(qr)
    db.commit()

    return QRGenerateOut(
        session_id=session.id,
        token=token_str,
        expires_at=expires_at.isoformat(),
    )


@router.post("/scan-qr")
def scan_qr_token(
    payload: QRScanIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    qr = db.scalar(
        select(AttendanceQrToken).where(
            AttendanceQrToken.token_hash == token_hash,
            AttendanceQrToken.expires_at > datetime.now(timezone.utc),
        )
    )
    if qr is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "QR kod muddati tugagan yoki noto'g'ri")

    session = db.get(ClassSession, qr.session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dars mashg'uloti topilmadi")

    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session.id,
            AttendanceRecord.student_id == user.id,
        )
    )
    if record is None:
        record = AttendanceRecord(
            center_id=session.center_id,
            session_id=session.id,
            student_id=user.id,
            status=AttStatus.present,
            source=AttSource.qr,
            marked_at=datetime.now(timezone.utc),
            confirmed_by_teacher=True,
        )
        db.add(record)
    else:
        record.status = AttStatus.present
        record.source = AttSource.qr

    db.commit()
    return {
        "status": "ok",
        "message": f"Davomat muvaffaqiyatli belgilandi: {user.full_name} darsga keldi!",
    }


@router.get("/sessions/{session_id}/records", response_model=list[AttendanceRecordOut])
def get_attendance_records(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_tenant_or_404(db, ClassSession, session_id, user)
    records = db.scalars(
        select(AttendanceRecord).where(AttendanceRecord.session_id == session.id)
    ).all()
    return [
        AttendanceRecordOut(
            id=r.id,
            session_id=r.session_id,
            student_id=r.student_id,
            status=r.status.value,
            source=r.source.value,
            marked_at=r.marked_at.isoformat(),
        )
        for r in records
    ]
