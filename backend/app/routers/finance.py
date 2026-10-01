from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_tenant_or_404, require_roles, tenant_select
from ..models import Group, Payment, PaymentKind, Role, User
from ..schemas import FinanceSummaryOut, PaymentCreate, PaymentOut
from ..services.audit import log_action

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/payments", response_model=list[PaymentOut])
def list_payments(
    user: User = Depends(require_roles(Role.super_admin, Role.center_admin)),
    db: Session = Depends(get_db),
):
    stmt = tenant_select(Payment, user).order_by(Payment.created_at.desc())
    payments = db.scalars(stmt).all()
    return [
        PaymentOut(
            id=p.id,
            student_id=p.student_id,
            group_id=p.group_id,
            amount=p.amount,
            period=p.period,
            method=p.method,
            note=p.note,
            created_at=p.created_at.isoformat(),
        )
        for p in payments
    ]


@router.post("/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    user: User = Depends(require_roles(Role.super_admin, Role.center_admin)),
    db: Session = Depends(get_db),
):
    student = get_tenant_or_404(db, User, payload.student_id, user)
    if payload.group_id:
        get_tenant_or_404(db, Group, payload.group_id, user)

    payment = Payment(
        center_id=student.center_id,
        student_id=student.id,
        group_id=payload.group_id,
        kind=PaymentKind.payment,
        amount=payload.amount,
        period=payload.period,
        method=payload.method,
        note=payload.note,
        created_by=user.id,
    )
    db.add(payment)
    log_action(db, user, "create_payment", "payment", payment.id)
    db.commit()

    return PaymentOut(
        id=payment.id,
        student_id=payment.student_id,
        group_id=payment.group_id,
        amount=payment.amount,
        period=payment.period,
        method=payment.method,
        note=payment.note,
        created_at=payment.created_at.isoformat(),
    )


@router.get("/summary", response_model=FinanceSummaryOut)
def get_finance_summary(
    period: str | None = None,
    user: User = Depends(require_roles(Role.super_admin, Role.center_admin)),
    db: Session = Depends(get_db),
):
    current_period = period or date.today().strftime("%Y-%m")
    stmt = tenant_select(Payment, user).where(Payment.period == current_period)

    total_revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.id.in_(select(Payment.id).from_statement(stmt))
        )
    ) or 0

    count = db.scalar(
        select(func.count(Payment.id)).where(
            Payment.id.in_(select(Payment.id).from_statement(stmt))
        )
    ) or 0

    return FinanceSummaryOut(
        total_revenue=int(total_revenue),
        payment_count=int(count),
        period=current_period,
    )
