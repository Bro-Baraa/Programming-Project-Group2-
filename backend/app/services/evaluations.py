"""Evaluation service layer orchestration."""

from datetime import datetime, UTC
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.models import Competency, Evaluation, EvaluationRule, Internship
from app.schemas import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationWithScoreResponse,
    EvaluationRuleUpdate,
)
from .common import ensure_internship_access, get_active_competency_profile


def list_evaluations(db: Session, current_user, internship_id: int) -> List[Evaluation]:
    internship = get_internship_or_404(db, internship_id)
    ensure_internship_access(current_user, internship)
    return (
        db.query(Evaluation)
        .options(joinedload(Evaluation.rules).joinedload(EvaluationRule.competency))
        .filter(Evaluation.internship_id == internship_id)
        .all()
    )


def create_evaluation(
    db: Session, current_user, internship_id: int, data: EvaluationCreate
) -> Evaluation:
    internship = get_internship_or_404(db, internship_id)
    ensure_internship_access(current_user, internship)
    ensure_internship_is_evaluable(internship)
    ensure_final_not_exists(db, internship_id, data.eval_type)

    # Students can only create self-evaluations for their own internship
    if current_user.role == "student":
        if data.eval_type not in ("tussentijds", "self"):
            raise HTTPException(
                status_code=403,
                detail="Students can only create tussentijds evaluations",
            )
        if internship.student_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized for this internship"
            )

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

    profile_id = internship.competency_profile_id
    if not profile_id:
        # Fallback: if no profile was captured (legacy internships), use the active one
        profile = get_active_competency_profile(db)
        if not profile:
            raise HTTPException(
                status_code=400, detail="No active competency profile found"
            )
        profile_id = profile.id

    seed_rules_from_active_profile(db, evaluation.id, profile_id)

    db.commit()
    db.refresh(evaluation)
    return evaluation


def get_evaluation_with_score(
    db: Session, current_user, evaluation_id: int
) -> EvaluationWithScoreResponse:
    evaluation = get_evaluation_or_404(db, evaluation_id)
    ensure_internship_access(current_user, evaluation.internship)
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
        raise HTTPException(
            status_code=400, detail="Cannot update finalized evaluation"
        )

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

    for rule in evaluation.rules:
        if rule.competency:
            rule.weight_snapshot = rule.competency.weight

    db.flush()
    db.refresh(evaluation)

    return evaluation, calculate_evaluation_score(db, evaluation)


# ─── Private helpers (inlined from evaluation_access / evaluation_lifecycle / evaluation_scoring)


def get_internship_or_404(db: Session, internship_id: int) -> Internship:
    internship = db.query(Internship).filter(Internship.id == internship_id).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    return internship


def get_evaluation_or_404(db: Session, evaluation_id: int) -> Evaluation:
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


def ensure_rule_update_access(current_user, internship: Internship) -> None:
    if current_user.role == "student":
        ensure_internship_access(current_user, internship)
    if current_user.role in ["teacher", "mentor"]:
        ensure_internship_access(
            current_user, internship, "Not authorized for this internship"
        )


def ensure_internship_is_evaluable(internship) -> None:
    if internship.status not in ["Lopend", "Afgerond"]:
        raise HTTPException(
            status_code=400, detail="Can only evaluate ongoing or completed internships"
        )


def ensure_final_not_exists(db: Session, internship_id: int, eval_type: str) -> None:
    if eval_type != "final":
        return
    existing = (
        db.query(Evaluation)
        .filter(
            Evaluation.internship_id == internship_id, Evaluation.eval_type == "final"
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Final evaluation already exists")


def seed_rules_from_active_profile(
    db: Session, evaluation_id: int, profile_id: int
) -> None:
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
    if evaluation.finalized:
        raise HTTPException(status_code=400, detail="Evaluation already finalized")
    if evaluation.evaluator_id == current_user.id:
        return
    if (
        current_user.role == "teacher"
        and evaluation.internship.teacher_id == current_user.id
    ):
        return
    raise HTTPException(
        status_code=403, detail="Only the evaluator or assigned teacher can finalize"
    )


def ensure_all_rules_scored(db: Session, evaluation_id: int) -> None:
    rules = (
        db.query(EvaluationRule)
        .filter(EvaluationRule.evaluation_id == evaluation_id)
        .all()
    )
    missing = [rule.id for rule in rules if rule.score is None]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot finalize: missing scores for competencies: {missing}",
        )


def mark_finalized(evaluation: Evaluation) -> None:
    evaluation.finalized = True
    evaluation.status = "afgerond"
    evaluation.finalized_at = datetime.now(UTC)


def calculate_evaluation_score(db: Session, evaluation: Evaluation) -> dict:
    rules = (
        db.query(EvaluationRule)
        .options(joinedload(EvaluationRule.competency))
        .filter(EvaluationRule.evaluation_id == evaluation.id)
        .all()
    )
    if not rules:
        return {"total_weight": 0, "achieved_weight": 0, "weighted_score": None}

    total_weight = 0
    achieved_weight = 0
    all_scored = True

    for rule in rules:
        competency = rule.competency
        if competency:
            weight = (
                rule.weight_snapshot
                if rule.weight_snapshot is not None
                else competency.weight
            )
            total_weight += weight
            if rule.score is not None:
                achieved_weight += (rule.score / 5.0) * weight
            else:
                all_scored = False

    weighted_score = (
        (achieved_weight / total_weight * 100)
        if total_weight > 0 and all_scored
        else None
    )

    return {
        "total_weight": total_weight,
        "achieved_weight": achieved_weight,
        "weighted_score": weighted_score,
    }
