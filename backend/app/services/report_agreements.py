"""Agreement report helpers."""

from typing import List
from sqlalchemy.orm import Session

from app.models import Internship
from app.schemas import AgreementStatusItem, UserResponse
from .report_common import apply_role_filter


def get_agreement_status_report(db: Session, current_user) -> List[AgreementStatusItem]:
    """Return the agreement overview scoped to the caller's visibility."""
    query = db.query(Internship).filter(
        Internship.status.in_(
            ["Goedgekeurd", "Overeenkomst Ingediend", "Lopend", "Afgerond"]
        )
    )

    query = apply_role_filter(query, current_user)

    result: List[AgreementStatusItem] = []
    for internship in query.all():
        agreement_status = "Niet Ingediend"
        uploaded_at = None

        if internship.agreement:
            agreement_status = internship.agreement.status
            uploaded_at = internship.agreement.uploaded_at

        result.append(
            AgreementStatusItem(
                internship_id=internship.id,
                student=UserResponse.model_validate(internship.student),
                status=internship.status,
                agreement_status=agreement_status,
                uploaded_at=uploaded_at,
            )
        )

    return result
