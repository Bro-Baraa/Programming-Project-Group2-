"""Dashboard and reporting endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas import DashboardStats, AgreementStatusItem, FinalReportItem
from app.auth import get_current_active_user, require_any_staff
from app.services.reports import (
    get_dashboard_stats as get_dashboard_stats_svc,
    get_agreement_status_report as get_agreement_status_report_svc,
    get_final_report as get_final_report_svc,
)

router = APIRouter(prefix="/internships", tags=["reports"])


@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get dashboard statistics - filtered by role"""
    return get_dashboard_stats_svc(db, current_user)


@router.get("/reports/agreements", response_model=List[AgreementStatusItem])
def get_agreement_status_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    """US-26: Admin view of agreement status for all students"""
    return get_agreement_status_report_svc(db, current_user)


@router.get("/{internship_id}/final-report", response_model=FinalReportItem)
def get_final_report(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-19: Generate final report for a student"""
    return get_final_report_svc(db, current_user, internship_id)
