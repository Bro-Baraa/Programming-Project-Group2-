"""Agreement endpoints."""

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
from app.services.lifecycle import InternshipLifecycle, DEFAULT_CONFIG
from app.services.audit import log_event

router = APIRouter(prefix="/internships", tags=["agreements"])


@router.post("/{internship_id}/agreement", response_model=AgreementResponse)
def upload_agreement_endpoint(
    internship_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):

    lifecycle = InternshipLifecycle(db, DEFAULT_CONFIG)
    result = lifecycle.upload_agreement(
        internship_id=internship_id,
        actor=current_user,
        file_stream=file.file,
        filename=file.filename,
        content_type=file.content_type,
    )
    log_event(
        db,
        "agreement.upload",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail="Overeenkomst geüpload",
    )
    return result.agreement


def _get_internship_with_agreement(db: Session, internship_id: int) -> Internship:

    internship = (
        db.query(Internship)
        .options(
            joinedload(Internship.agreement),
        )
        .filter(Internship.id == internship_id)
        .first()
    )
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    return internship


@router.get("/{internship_id}/agreement", response_model=AgreementResponse)
def get_agreement(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

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

    lifecycle = InternshipLifecycle(db, DEFAULT_CONFIG)
    result = lifecycle.validate_agreement(
        internship_id=internship_id,
        actor=current_user,
        insurance_verified=update.insurance_verified,
        agreement_status=update.status,
    )
    log_event(
        db,
        "agreement.validate",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail=f"Overeenkomst gevalideerd: {update.status}",
    )
    return result.agreement
