"""Authenticated "me" endpoints.

Aggregated dashboard and personal data for the currently logged-in user.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import get_current_active_user
from app.services.dashboard import get_me_dashboard
from app.schemas import MeDashboardResponse

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/dashboard", response_model=MeDashboardResponse)
def me_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get everything the current user needs for their primary dashboard.

    Returns a single payload containing:
    - User info
    - All visible internships with rich summaries
    - Computed stats (counts by status)
    - Actionable alerts (things needing attention)

    This replaces the frontend calling:
    - GET /internships
    - GET /internships/{id}/logbooks
    - GET /internships/{id}/evaluations
    - GET /internships/{id}/feedback
    - GET /internships/stats/dashboard

    With a single call.
    """
    return get_me_dashboard(db, current_user)
