"""Overeenkomst endpoints."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Internship, User
from app.schemas import AgreementResponse, AgreementUpdate
from app.auth import (
    get_current_active_user,
    require_student,
    require_committee_or_admin,
)
from app.services.common import ensure_internship_access
from app.services.lifecycle import InternshipLifecycle, LifecycleConfig

router = APIRouter(prefix="/internships", tags=["agreements"])


@router.post("/{internship_id}/agreement", response_model=AgreementResponse)
def upload_agreement_endpoint(
    internship_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """US-04: Student uploadt stageovereenkomst (enkel PDF).

    Alleen toegestaan als het voorstel goedgekeurd is.
    """
    lifecycle = InternshipLifecycle(db, LifecycleConfig(agreements_dir=Path("uploads/agreements")))
    result = lifecycle.upload_agreement(
        internship_id=internship_id,
        actor=current_user,
        file_stream=file.file,
        filename=file.filename,
        content_type=file.content_type,
    )
    return result.internship.agreement


def _get_internship_with_agreement(db: Session, internship_id: int) -> Internship:
    """Haalt stage op met overeenkomst eager-loaded, of geeft 404."""
    internship = db.query(Internship).options(
        joinedload(Internship.agreement),
    ).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    return internship


@router.get("/{internship_id}/agreement", response_model=AgreementResponse)
def get_agreement(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Haalt overeenkomst details op"""
    internship = _get_internship_with_agreement(db, internship_id)
    ensure_internship_access(current_user, internship)
    if not internship.agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return internship.agreement


@router.get("/{internship_id}/agreement/download")
def download_agreement(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Downloadt de geüploade overeenkomst PDF."""
    internship = _get_internship_with_agreement(db, internship_id)
    ensure_internship_access(current_user, internship)
    if not internship.agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    file_path = Path(internship.agreement.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Agreement file not found on disk")

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"stage_overeenkomst_{internship_id}.pdf",
    )


@router.patch("/{internship_id}/agreement", response_model=AgreementResponse)
def validate_agreement_endpoint(
    internship_id: int,
    update: AgreementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_committee_or_admin),
):
    """US-13, US-26: Commissie/admin valideert overeenkomst.

    Status: Gevalideerd of Onvolledig.
    """
    lifecycle = InternshipLifecycle(db, LifecycleConfig(agreements_dir=Path("uploads/agreements")))
    result = lifecycle.validate_agreement(
        internship_id=internship_id,
        actor=current_user,
        insurance_verified=update.insurance_verified,
        agreement_status=update.status,
    )
    return result.internship.agreement
