"""Agreement (Overeenkomst) endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import Internship, User
from app.schemas import AgreementResponse, AgreementUpdate
from app.auth import (
    get_current_active_user,
    require_student,
    require_committee_or_admin,
)
from app.services.common import ensure_internship_access
from app.services.agreements import upload_agreement, validate_agreement

router = APIRouter(prefix="/internships", tags=["agreements"])

UPLOAD_DIR = "uploads"
AGREEMENTS_DIR = os.path.join(UPLOAD_DIR, "agreements")
os.makedirs(AGREEMENTS_DIR, exist_ok=True)


@router.post("/{internship_id}/agreement", response_model=AgreementResponse)
def upload_agreement_endpoint(
    internship_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """US-04: Student uploads internship agreement (PDF only)

    Only allowed when proposal is approved (Goedgekeurd)
    """
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    upload_agreement(db, internship, current_user, file, AGREEMENTS_DIR)
    return internship.agreement


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
    """US-13, US-26: Committee/admin validates agreement

    Status: Gevalideerd or Onvolledig
    """
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    if not internship.agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    validate_agreement(db, internship, update)
    return internship.agreement
