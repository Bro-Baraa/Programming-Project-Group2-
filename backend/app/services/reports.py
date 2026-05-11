"""Dashboard and reporting service layer orchestration."""
from sqlalchemy.orm import Session
from typing import List

from app.schemas import DashboardStats, AgreementStatusItem, FinalReportItem
from .report_dashboard import get_dashboard_stats as get_dashboard_stats_impl
from .report_agreements import (
    get_agreement_status_report as get_agreement_status_report_impl,
)
from .report_final import get_final_report as get_final_report_impl


def get_dashboard_stats(db: Session, current_user) -> DashboardStats:
    """Compute the role-scoped internship dashboard summary."""
    return get_dashboard_stats_impl(db, current_user)


def get_agreement_status_report(
    db: Session, current_user
) -> List[AgreementStatusItem]:
    """Return the agreement overview scoped to the caller's visibility."""
    return get_agreement_status_report_impl(db, current_user)


def get_final_report(
    db: Session, current_user, internship_id: int
) -> FinalReportItem:
    """Build the final internship report used by the router response."""
    return get_final_report_impl(db, current_user, internship_id)
