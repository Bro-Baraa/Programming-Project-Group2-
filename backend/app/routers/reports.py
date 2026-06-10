"""Dashboard and reporting endpoints."""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Internship
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


@router.get("/reports/export/csv")
def export_internships_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    """US-28: Exporteer alle stages als CSV."""
    internships = db.query(Internship).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student", "Email", "Bedrijf", "Sector", "Status",
        "Startdatum", "Einddatum", "Docent", "Mentor",
        "Voorstel Status", "Overeenkomst Status"
    ])
    for i in internships:
        writer.writerow([
            f"{i.student.first_name} {i.student.last_name}" if i.student else "",
            i.student.email if i.student else "",
            i.company.name if i.company else "",
            i.company.sector if i.company else "",
            i.status,
            str(i.start_date) if i.start_date else "",
            str(i.end_date) if i.end_date else "",
            f"{i.teacher.first_name} {i.teacher.last_name}" if i.teacher else "",
            f"{i.mentor.first_name} {i.mentor.last_name}" if i.mentor else "",
            i.proposal.status if i.proposal else "",
            i.agreement.status if i.agreement else "",
        ])

    output.seek(0)
    filename = f"stage_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
