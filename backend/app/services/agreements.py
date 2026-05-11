"""Agreement service layer."""
import os
import shutil
from datetime import datetime, UTC
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models import Internship, Agreement
from app.schemas import AgreementUpdate


def upload_agreement(
    db: Session,
    internship: Internship,
    current_user,
    file: UploadFile,
    agreements_dir: str,
) -> None:
    """Persist a PDF agreement and move the internship forward."""
    if internship.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if internship.status != "Goedgekeurd":
        raise HTTPException(
            status_code=400,
            detail="Can only upload agreement after proposal is approved",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    filename = f"agreement_{internship.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(agreements_dir, filename)

    # Ensure directory exists
    os.makedirs(agreements_dir, exist_ok=True)

    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        # Close the uploaded file if it has a close method
        if hasattr(file.file, 'close') and callable(file.file.close):
            file.file.close()

    if internship.agreement:
        agreement = internship.agreement
        agreement.file_path = filepath
        agreement.status = "Ingediend"
        agreement.uploaded_at = datetime.now(UTC)
    else:
        agreement = Agreement(
            internship_id=internship.id,
            file_path=filepath,
            status="Ingediend",
            uploaded_at=datetime.now(UTC),
        )
        db.add(agreement)

    internship.status = "Overeenkomst Ingediend"
    db.commit()
    db.refresh(agreement)


def validate_agreement(
    db: Session,
    internship: Internship,
    update: AgreementUpdate,
) -> None:
    """Update agreement validation and advance internship status when approved."""
    if not internship.agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    if update.status not in ["Gevalideerd", "Onvolledig"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    agreement = internship.agreement

    if update.insurance_verified is not None:
        agreement.insurance_verified = update.insurance_verified
    if update.status is not None:
        agreement.status = update.status

    if agreement.status == "Gevalideerd":
        agreement.validated_at = datetime.now(UTC)
        internship.status = "Lopend"

    db.commit()
    db.refresh(agreement)
