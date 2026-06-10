"""Dashboard aggregation schemas.

These schemas power the /me/dashboard endpoint which returns
everything a user needs for their primary view in a single call.
"""

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

from .user import UserResponse
from .internship import InternshipListResponse
from .logbook import LogbookResponse
from .evaluation import EvaluationResponse
from .feedback import FeedbackResponse


class InternshipDashboardItem(BaseModel):
    """Rich internship summary for dashboard list views."""

    model_config = ConfigDict(from_attributes=True)

    internship: InternshipListResponse
    proposal_status: Optional[str] = None
    agreement_status: Optional[str] = None
    agreement_uploaded: bool = False

    # Logbook summary (computed)
    total_weeks: int = 0
    logbooks_submitted: int = 0
    logbooks_missing: int = 0
    logbooks_draft: int = 0
    next_due_week: Optional[int] = None

    # Evaluation summary
    evaluations_count: int = 0
    evaluations_finalized: int = 0
    latest_evaluation_status: Optional[str] = None

    # Recent feedback (last 3 items)
    recent_feedback: List[FeedbackResponse] = []


class UserDashboardStats(BaseModel):
    """Role-scoped statistics for a single user's dashboard."""

    total_internships: int = 0
    pending_approval: int = 0
    approved: int = 0
    rejected: int = 0
    ongoing: int = 0
    completed: int = 0
    agreements_received: int = 0
    agreements_pending: int = 0
    agreements_validated: int = 0


class DashboardAlert(BaseModel):
    """Something that needs the user's attention."""

    severity: str  # info, warning, error
    message: str
    action_url: Optional[str] = None  # e.g. "?view=voorstel"
    entity_type: Optional[str] = None  # internship, logbook, evaluation
    entity_id: Optional[int] = None


class MeDashboardResponse(BaseModel):
    """Everything the frontend needs for the primary dashboard view."""

    model_config = ConfigDict(from_attributes=True)

    user: UserResponse
    role: str

    # Internships visible to this user
    internships: List[InternshipDashboardItem] = []

    # Computed stats
    stats: UserDashboardStats

    # Things needing attention
    alerts: List[DashboardAlert] = []

    # Timestamp for cache-busting
    generated_at: datetime
