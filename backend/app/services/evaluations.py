"""Evaluation service layer orchestration."""
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from typing import List

from app.models import Evaluation, EvaluationRule
from app.schemas import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationWithScoreResponse,
    EvaluationRuleUpdate,
)
from .common import get_active_competency_profile
from .evaluation_access import (
    ensure_can_access_internship,
    ensure_rule_update_access,
    get_evaluation_or_404,
    get_internship_or_404,
    get_rule_or_404,
)
from .evaluation_lifecycle import (
    ensure_all_rules_scored,
    ensure_can_finalize,
    ensure_final_not_exists,
    ensure_internship_is_evaluable,
    mark_finalized,
    seed_rules_from_active_profile,
)
from .evaluation_scoring import calculate_evaluation_score


def list_evaluations(
    db: Session, current_user, internship_id: int
) -> List[Evaluation]:
    internship = get_internship_or_404(db, internship_id)
    ensure_can_access_internship(current_user, internship)
    return (
        db.query(Evaluation)
        .options(
            joinedload(Evaluation.rules).joinedload(EvaluationRule.competency)
        )
        .filter(Evaluation.internship_id == internship_id)
        .all()
    )


def create_evaluation(
    db: Session, current_user, internship_id: int, data: EvaluationCreate
) -> Evaluation:
    internship = get_internship_or_404(db, internship_id)
    ensure_can_access_internship(current_user, internship)
    ensure_internship_is_evaluable(internship)
    ensure_final_not_exists(db, internship_id, data.eval_type)

    evaluation = Evaluation(
        internship_id=internship_id,
        evaluator_id=current_user.id,
        eval_type=data.eval_type,
        status="concept",
        comments=data.comments,
        finalized=False,
    )

    db.add(evaluation)
    db.flush()

    # ── Use the internship's captured competency profile, not the current active one ──
    profile_id = internship.competency_profile_id
    if not profile_id:
        # Fallback: if no profile was captured (legacy internships), use the active one
        profile = get_active_competency_profile(db)
        if not profile:
            raise HTTPException(status_code=400, detail="No active competency profile found")
        profile_id = profile.id

    seed_rules_from_active_profile(db, evaluation.id, profile_id)

    db.commit()
    db.refresh(evaluation)
    return evaluation


def get_evaluation_with_score(
    db: Session, current_user, evaluation_id: int
) -> EvaluationWithScoreResponse:
    evaluation = get_evaluation_or_404(db, evaluation_id)
    ensure_can_access_internship(current_user, evaluation.internship)
    score_data = calculate_evaluation_score(db, evaluation)

    return EvaluationWithScoreResponse(
        **EvaluationResponse.model_validate(evaluation).model_dump(),
        **score_data,
    )


def update_evaluation_rule(
    db: Session,
    current_user,
    evaluation_id: int,
    rule_id: int,
    update: EvaluationRuleUpdate,
) -> EvaluationRule:
    evaluation = get_evaluation_or_404(db, evaluation_id)

    if evaluation.finalized:
        raise HTTPException(status_code=400, detail="Cannot update finalized evaluation")

    rule = get_rule_or_404(db, evaluation_id, rule_id)

    internship = evaluation.internship
    ensure_rule_update_access(current_user, internship)

    if current_user.role == "student":
        if update.student_description is not None:
            rule.student_description = update.student_description

    if current_user.role in ["teacher", "mentor", "committee", "admin"]:
        if update.score is not None:
            if update.score < 1 or update.score > 5:
                raise HTTPException(
                    status_code=400, detail="Score must be between 1 and 5"
                )
            rule.score = update.score
        if update.evaluator_feedback is not None:
            rule.evaluator_feedback = update.evaluator_feedback

    db.commit()
    db.refresh(rule)
    return rule


def finalize_evaluation(
    db: Session, evaluation: Evaluation, current_user
) -> tuple[Evaluation, dict]:
    ensure_can_finalize(evaluation, current_user)
    ensure_all_rules_scored(db, evaluation.id)
    mark_finalized(evaluation)

    db.commit()
    db.refresh(evaluation)

    return evaluation, calculate_evaluation_score(db, evaluation)
