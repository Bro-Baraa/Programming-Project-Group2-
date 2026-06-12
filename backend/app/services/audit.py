"""Audit log service."""

from datetime import datetime, UTC
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog, User


def log_event(
    db: Session,
    action: str,
    *,
    user: Optional[User] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    detail: Optional[str] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    ip = None
    if request and request.client:
        ip = request.client.host

    entry = AuditLog(
        action=action,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_role=user.role if user else None,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        ip_address=ip,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
