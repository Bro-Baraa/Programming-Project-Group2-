"""Dashboard and reporting schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from .user import UserResponse
from .evaluation import EvaluationWithScoreResponse


class DashboardStats(BaseModel):
    total_internships: int
    pending_approval: int
    approved: int
    rejected: int
    ongoing: int
    completed: int
    stopped: int
    agreements_received: int
    agreements_pending: int


class AgreementStatusItem(BaseModel):
    """For US-26: admin overview of agreement status"""

    internship_id: int
    student: UserResponse
    status: str
    agreement_status: str
    uploaded_at: Optional[datetime] = None


class FinalReportItem(BaseModel):
    """For US-19: final report per student"""

    internship_id: int
    student: UserResponse
    company_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    # Proposal info
    proposal_status: str
    proposal_submitted_at: Optional[datetime] = None

    # Agreement info
    agreement_status: str
    agreement_uploaded_at: Optional[datetime] = None

    # Logbook summary
    total_days: int
    submitted_logbooks: int
    missing_logbooks: int

    # Evaluations
    final_evaluation: Optional[EvaluationWithScoreResponse] = None
    weighted_final_score: Optional[float] = None
