"""Final report generation helpers."""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models import Internship, Logbook, Evaluation, EvaluationRule
from app.schemas import (
    FinalReportItem,
    UserResponse,
    EvaluationResponse,
    EvaluationWithScoreResponse,
)
from .common import ensure_internship_access
from .evaluations import calculate_evaluation_score


def get_final_report(db: Session, current_user, internship_id: int) -> FinalReportItem:
    """Build the final internship report used by the router response."""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    total_days = 0
    if internship.start_date and internship.end_date:
        total_days = (internship.end_date - internship.start_date).days + 1

    submitted_logbooks = (
        db.query(Logbook)
        .filter(
            Logbook.internship_id == internship_id,
            Logbook.status == "submitted",
        )
        .count()
    )
    final_eval = (
        db.query(Evaluation)
        .options(joinedload(Evaluation.rules).joinedload(EvaluationRule.competency))
        .filter(
            Evaluation.internship_id == internship_id,
            Evaluation.eval_type == "final",
            Evaluation.finalized == True,
        )
        .first()
    )

    final_eval_response = None
    weighted_score = None

    if final_eval:
        score_data = calculate_evaluation_score(db, final_eval)
        final_eval_response = EvaluationWithScoreResponse(
            **EvaluationResponse.model_validate(final_eval).model_dump(),
            **score_data,
        )
        weighted_score = score_data["weighted_score"]

    student = internship.student
    if student is None:
        raise HTTPException(
            status_code=500, detail="Internship has no associated student"
        )

    return FinalReportItem(
        internship_id=internship.id,
        student=UserResponse.model_validate(student),
        company_name=internship.company.name if internship.company else None,
        start_date=internship.start_date,
        end_date=internship.end_date,
        proposal_status=(
            internship.proposal.status if internship.proposal else "Onbekend"
        ),
        proposal_submitted_at=(
            internship.proposal.submitted_at if internship.proposal else None
        ),
        agreement_status=(
            internship.agreement.status if internship.agreement else "Niet Ingediend"
        ),
        agreement_uploaded_at=(
            internship.agreement.uploaded_at if internship.agreement else None
        ),
        total_days=total_days,
        submitted_logbooks=submitted_logbooks,
        missing_logbooks=max(0, total_days - submitted_logbooks),
        final_evaluation=final_eval_response,
        weighted_final_score=weighted_score,
    )
