from fastapi import Request
from sqlalchemy.orm import Session

from ..models import AuditLog, User
from ..models.base import utcnow


def log_action(
    db: Session,
    actor: User | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    data: dict | None = None,
    request: Request | None = None,
    center_id: int | None = None,
) -> None:
    """Audit yozuvini qo'shadi (commit chaqiruvchi tomonidan qilinadi)."""
    db.add(
        AuditLog(
            created_at=utcnow(),
            center_id=center_id if center_id is not None else (actor.center_id if actor else None),
            user_id=actor.id if actor else None,
            action=action,
            entity=entity,
            entity_id=entity_id,
            data=data,
            ip=request.client.host if request and request.client else None,
        )
    )
