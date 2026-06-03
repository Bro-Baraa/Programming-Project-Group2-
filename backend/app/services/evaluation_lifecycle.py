"""Evaluation lifecycle and transition helpers."""
from datetime import datetime, UTC
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Evaluation, EvaluationRule, Competency


def ensure_internship_is_evaluable(internship) -> None:
    """Guard that evaluations can be created for the internship status."""
    if internship.status not in ["Lopend", "Afgerond"]:
        raise HTTPException(
            status_code=400, detail="Can only evaluate ongoing or completed internships"
        )


def ensure_final_not_exists(db: Session, internship_id: int, eval_type: str) -> None:
    """Guard against duplicate final evaluation."""
    if eval_type != "final":
        return

    existing_final = (
        db.query(Evaluation)
        .filter(
            Evaluation.internship_id == internship_id,
            Evaluation.eval_type == "final",
        )
        .first()
    )
    if existing_final:
        raise HTTPException(status_code=400, detail="Final evaluation already exists")


def seed_rules_from_active_profile(db: Session, evaluation_id: int, profile_id: int) -> None:
    """Create rule rows for all active competencies in the selected profile."""
    competencies = (
        db.query(Competency)
        .filter(Competency.profile_id == profile_id, Competency.active == True)
        .all()
    )

    for competency in competencies:
        db.add(
            EvaluationRule(
                evaluation_id=evaluation_id,
                competency_id=competency.id,
                score=None,
                student_description=None,
                evaluator_feedback=None,
            )
        )


def ensure_can_finalize(evaluation: Evaluation, current_user) -> None:
    """Guard finalize permissions and state."""
    if evaluation.evaluator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the evaluator can finalize")

    if evaluation.finalized:
        raise HTTPException(status_code=400, detail="Evaluation already finalized")


def ensure_all_rules_scored(db: Session, evaluation_id: int) -> None:
    """Guard that each rule has a score before finalization."""
    rules = (
        db.query(EvaluationRule)
        .filter(EvaluationRule.evaluation_id == evaluation_id)
        .all()
    )
    missing_scores = [rule.id for rule in rules if rule.score is None]

    if missing_scores:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot finalize: missing scores for competencies: {missing_scores}",
        )


def mark_finalized(evaluation: Evaluation) -> None:
    """Apply finalization state on evaluation."""
    evaluation.finalized = True
    evaluation.status = "afgerond"
    evaluation.finalized_at = datetime.now(UTC)
