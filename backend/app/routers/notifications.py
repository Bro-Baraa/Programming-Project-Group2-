"""
Notification endpoints.

Allows the logged-in user to fetch their own notifications and mark them as read.
Notifications are created server-side (never by the client directly).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import Notification, User
from app.auth import get_current_active_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    """What the frontend receives for each notification."""

    id: int
    message: str
    internship_id: int | None
    link_view: str | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[NotificationResponse])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Return all notifications for the logged-in user, newest first.
    The frontend polls this every 30 seconds to keep the bell up to date.
    """
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        # Limit to last 50 so the dropdown doesn't become overwhelming
        .limit(50)
        .all()
    )
    return notifications


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Mark a single notification as read.
    Only the owner of the notification can mark it as read.
    """
    notification = (
        db.query(Notification).filter(Notification.id == notification_id).first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notificatie niet gevonden")

    # Make sure users can only mark their own notifications as read
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Niet toegestaan")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/read-all", response_model=List[NotificationResponse])
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Mark all of the logged-in user's unread notifications as read at once.
    Called when the user opens the bell dropdown.
    """
    unread = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .all()
    )
    for n in unread:
        n.is_read = True
    db.commit()

    # Return the full updated list so the frontend can re-render
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
