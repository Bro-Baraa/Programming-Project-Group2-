"""
Notification helper service.

This module provides a single `notify()` function that creates a notification
for a user. It is intentionally simple — just call notify() after any action
that impacts another user and it will store it in the database.

In the future, this is also the place to add email sending:
just extend notify() to optionally send an email via SMTP or a mail service.

Usage example:
    from app.services.notifications import notify
    notify(db, user_id=student.id, message="Je voorstel is goedgekeurd!", internship_id=internship.id, link_view="dashboard")
"""

from sqlalchemy.orm import Session
from app.models import Notification


def notify(
    db: Session,
    user_id: int,
    message: str,
    internship_id: int | None = None,
    link_view: str | None = None,
) -> Notification:
    """
    Create a notification for a user.

    Args:
        db:             Database session (will be flushed but NOT committed —
                        the caller's existing commit covers this).
        user_id:        The user who should receive the notification.
        message:        Human-readable message shown in the bell dropdown.
        internship_id:  Optional — links the notification to a specific internship.
        link_view:      Optional — the frontend view to navigate to on click.
                        e.g. "voorstellen", "logboek", "overeenkomsten", "dashboard"
                        The frontend builds: ?view={link_view}&internship={internship_id}

    Returns:
        The created Notification object.
    """
    notification = Notification(
        user_id=user_id,
        message=message,
        internship_id=internship_id,
        link_view=link_view,
    )
    db.add(notification)
    db.flush()  # get the id without committing — caller commits
    return notification
