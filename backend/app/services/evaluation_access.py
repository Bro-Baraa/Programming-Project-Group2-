"""Evaluation access and lookup helpers."""

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models import Internship, Evaluation, EvaluationRule
from .common import ensure_internship_access


def get_internship_or_404(db: Session, internship_id: int) -> Internship:
    """Return internship or raise 404."""
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    return internship


def get_evaluation_or_404(db: Session, evaluation_id: int) -> Evaluation:
    """Return evaluation or raise 404."""
    evaluation = (
        db.query(Evaluation)
        .options(joinedload(Evaluation.rules).joinedload(EvaluationRule.competency))
        .filter(Evaluation.id == evaluation_id)
        .first()
    )
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


def get_rule_or_404(db: Session, evaluation_id: int, rule_id: int) -> EvaluationRule:
    """Return evaluation rule or raise 404."""
    rule = (
        db.query(EvaluationRule)
        .filter(
            EvaluationRule.id == rule_id,
            EvaluationRule.evaluation_id == evaluation_id,
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Evaluation rule not found")
    return rule


def ensure_can_access_internship(
    current_user, internship: Internship, detail: str = "Not authorized"
) -> None:
    """Apply internship-level access rules."""
    ensure_internship_access(current_user, internship, detail)


def ensure_rule_update_access(current_user, internship: Internship) -> None:
    """Enforce role-sensitive access for evaluation rule updates."""
    if current_user.role == "student":
        ensure_internship_access(current_user, internship)

    if current_user.role in ["teacher", "mentor"]:
        ensure_internship_access(
            current_user, internship, "Not authorized for this internship"
        )
