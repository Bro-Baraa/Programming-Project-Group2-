"""Agreement (Overeenkomst) endpoints."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

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
    """US-04: Student uploads internship agreement (PDF only).

    Only allowed when proposal is approved (Goedgekeurd).
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


@router.get("/{internship_id}/agreement", response_model=AgreementResponse)
def get_agreement(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get agreement details"""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    if not internship.agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    return internship.agreement


@router.patch("/{internship_id}/agreement", response_model=AgreementResponse)
def validate_agreement_endpoint(
    internship_id: int,
    update: AgreementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_committee_or_admin),
):
    """US-13, US-26: Committee/admin validates agreement.

    Status: Gevalideerd or Onvolledig.
    """
    lifecycle = InternshipLifecycle(db, LifecycleConfig(agreements_dir=Path("uploads/agreements")))
    result = lifecycle.validate_agreement(
        internship_id=internship_id,
        actor=current_user,
        insurance_verified=update.insurance_verified,
        agreement_status=update.status,
    )
    return result.internship.agreement
