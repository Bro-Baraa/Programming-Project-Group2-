"""Audit log endpoints (admin only)."""

from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import AuditLog, User
from app.schemas import AuditLogResponse
from app.auth import require_admin
from app.dependencies import pagination

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    response: Response,
    action: Annotated[
        Optional[str], Query(description="Filter op actie, bijv. 'login'")
    ] = None,
    user_email: Annotated[
        Optional[str], Query(description="Filter op e-mail van gebruiker")
    ] = None,
    entity_type: Annotated[
        Optional[str], Query(description="Filter op entiteitstype, bijv. 'internship'")
    ] = None,
    pag: Annotated[dict, Depends(pagination)] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):

    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if user_email:
        query = query.filter(AuditLog.user_email.ilike(f"%{user_email}%"))
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.with_entities(func.count(AuditLog.id)).scalar()
    response.headers["X-Total-Count"] = str(total)

    skip = pag.get("skip", 0) if pag else 0
    limit = pag.get("limit", 50) if pag else 50

    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs
