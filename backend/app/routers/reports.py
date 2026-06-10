"""Dashboard and reporting endpoints."""
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas import DashboardStats, AgreementStatusItem, FinalReportItem
from app.auth import get_current_active_user, require_any_staff
from app.services import reports as _reports
from app.services.report_pdf import generate_final_report_pdf

router = APIRouter(prefix="/internships", tags=["reports"])


@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return _reports.get_dashboard_stats(db, current_user)


@router.get("/reports/agreements", response_model=List[AgreementStatusItem])
def get_agreement_status_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    return _reports.get_agreement_status_report(db, current_user)


@router.get("/{internship_id}/final-report", response_model=FinalReportItem)
def get_final_report(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return _reports.get_final_report(db, current_user, internship_id)


@router.get("/{internship_id}/final-report/pdf")
def get_final_report_pdf(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    pdf_path, student = generate_final_report_pdf(db, current_user, internship_id)
    filename = f"eindrapport_{student.first_name}_{student.last_name}.pdf"
    return FileResponse(
        str(pdf_path),
        media_type="application/pdf",
        filename=filename,
    )
