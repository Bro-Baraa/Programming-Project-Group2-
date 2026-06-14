"""Dashboard and reporting service layer."""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.models import Agreement, Internship, Logbook, Evaluation, EvaluationRule
from app.schemas import (
    AgreementStatusItem,
    DashboardStats,
    EvaluationResponse,
    EvaluationWithScoreResponse,
    FinalReportItem,
    UserResponse,
)
from .common import ensure_internship_access
from .evaluations import calculate_evaluation_score


def _apply_role_filter(query, user):
    if user.role == "student":
        return query.filter(Internship.student_id == user.id)
    if user.role == "mentor":
        return query.filter(Internship.mentor_id == user.id)
    if user.role == "teacher":
        return query.filter(Internship.teacher_id == user.id)
    return query


def get_dashboard_stats(db: Session, current_user) -> DashboardStats:
    base_query = _apply_role_filter(db.query(Internship), current_user)

    total = base_query.count()
    pending = base_query.filter(
        Internship.status.in_(["Ingediend", "In Beoordeling", "Aanpassingen Vereist"])
    ).count()
    approved = base_query.filter(Internship.status == "Goedgekeurd").count()
    rejected = base_query.filter(Internship.status == "Afgekeurd").count()
    ongoing = base_query.filter(Internship.status == "Lopend").count()
    completed = base_query.filter(Internship.status == "Afgerond").count()
    stopped = base_query.filter(Internship.status == "Stopgezet").count()

    internship_ids = [i.id for i in base_query.all()]
    if internship_ids:
        agreements_received = (
            db.query(Agreement)
            .filter(Agreement.internship_id.in_(internship_ids))
            .count()
        )
        agreements_validated = (
            db.query(Agreement)
            .filter(
                Agreement.internship_id.in_(internship_ids),
                Agreement.status == "Gevalideerd",
            )
            .count()
        )
    else:
        agreements_received = 0
        agreements_validated = 0

    return DashboardStats(
        total_internships=total,
        pending_approval=pending,
        approved=approved,
        rejected=rejected,
        ongoing=ongoing,
        completed=completed,
        stopped=stopped,
        agreements_received=agreements_received,
        agreements_pending=agreements_received - agreements_validated,
    )


def get_agreement_status_report(db: Session, current_user) -> List[AgreementStatusItem]:
    query = db.query(Internship).filter(
        Internship.status.in_(
            ["Goedgekeurd", "Overeenkomst Ingediend", "Lopend", "Afgerond"]
        )
    )
    query = _apply_role_filter(query, current_user)

    result = []
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


def get_final_report(db: Session, current_user, internship_id: int) -> FinalReportItem:
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")

    ensure_internship_access(current_user, internship)

    total_days = 0
    if internship.start_date and internship.end_date:
        total_days = (internship.end_date - internship.start_date).days + 1

    submitted_logbooks = (
        db.query(Logbook)
        .filter(Logbook.internship_id == internship_id, Logbook.status == "submitted")
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
