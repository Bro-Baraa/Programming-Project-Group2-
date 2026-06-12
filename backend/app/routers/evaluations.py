"""Evaluation endpoints."""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.database import get_db
from app.models import Evaluation, User
from app.schemas import (
    EvaluationResponse,
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationRuleResponse,
    EvaluationRuleUpdate,
    EvaluationWithScoreResponse,
)
from app.auth import get_current_active_user, require_teacher, require_any_staff
from app.services.common import ensure_internship_access
from app.services.evaluations import (
    create_evaluation as create_evaluation_svc,
    get_evaluation_with_score,
    list_evaluations as list_evaluations_svc,
    update_evaluation_rule as update_evaluation_rule_svc,
    finalize_evaluation as finalize_evaluation_svc,
)
from app.services.lifecycle import InternshipLifecycle, LifecycleConfig
from app.services.notifications import notify
from app.services.audit import log_event

router = APIRouter(prefix="/internships", tags=["evaluations"])


@router.get("/{internship_id}/evaluations", response_model=List[EvaluationResponse])
def list_evaluations(
    internship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-09, US-18: List evaluations for an internship"""
    return list_evaluations_svc(db, current_user, internship_id)


@router.post("/{internship_id}/evaluations", response_model=EvaluationResponse)
def create_evaluation(
    internship_id: int,
    data: EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-06, US-17, US-18: Create an evaluation (teacher, mentor, or student self-eval)."""
    result = create_evaluation_svc(db, current_user, internship_id, data)
    log_event(
        db,
        "evaluation.create",
        user=current_user,
        entity_type="internship",
        entity_id=internship_id,
        detail=f"Evaluatie aangemaakt: {data.eval_type}",
    )

    eval_label = (
        "eindevaluatie" if data.eval_type == "final" else "tussentijdse evaluatie"
    )
    evaluator_name = (
        f"{current_user.first_name} {current_user.last_name}"
        if current_user
        else "Je docent"
    )
    notify(
        db,
        user_id=result.internship.student_id,
        message=f"{evaluator_name} heeft een {eval_label} aangemaakt.",
        internship_id=internship_id,
        link_view="evaluatie",
    )
    db.commit()

    return result


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationWithScoreResponse)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get evaluation with calculated score"""
    return get_evaluation_with_score(db, current_user, evaluation_id)


@router.patch("/evaluations/{evaluation_id}", response_model=EvaluationResponse)
def update_evaluation(
    evaluation_id: int,
    update: EvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
):
    """US-18: Update evaluation comments (general remarks)"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    ensure_internship_access(
        current_user, evaluation.internship, "Not authorized to update this evaluation"
    )

    if evaluation.finalized:
        raise HTTPException(
            status_code=400, detail="Cannot update finalized evaluation"
        )

    if update.comments is not None:
        evaluation.comments = update.comments

    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.patch(
    "/evaluations/{evaluation_id}/rules/{rule_id}",
    response_model=EvaluationRuleResponse,
)
def update_evaluation_rule(
    evaluation_id: int,
    rule_id: int,
    update: EvaluationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """US-06, US-16, US-18, US-23: Update an evaluation rule

    Student adds description of what they learned
    Teacher/mentor adds score and feedback
    """
    return update_evaluation_rule_svc(db, current_user, evaluation_id, rule_id, update)


@router.post(
    "/evaluations/{evaluation_id}/finalize", response_model=EvaluationWithScoreResponse
)
def finalize_evaluation_endpoint(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """US-18: Finalize an evaluation - cannot be modified after.
    If this is a final evaluation, the internship is also marked as completed."""
    evaluation = (
        db.query(Evaluation)
        .options(joinedload(Evaluation.internship))
        .filter(Evaluation.id == evaluation_id)
        .first()
    )
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # finalize_evaluation_svc returns (Evaluation, dict) tuple
    finalized_eval, score_data = finalize_evaluation_svc(db, evaluation, current_user)

    if finalized_eval.eval_type == "final":
        lifecycle = InternshipLifecycle(
            db, LifecycleConfig(agreements_dir=Path("uploads/agreements"))
        )
        lifecycle.complete_internship(
            internship_id=finalized_eval.internship_id,
            actor=current_user,
        )

    db.commit()

    evaluator_name = (
        f"{current_user.first_name} {current_user.last_name}"
        if current_user
        else "Je docent"
    )
    eval_label = (
        "eindevaluatie"
        if finalized_eval.eval_type == "final"
        else "tussentijdse evaluatie"
    )
    notify(
        db,
        user_id=finalized_eval.internship.student_id,
        message=f"{evaluator_name} heeft je {eval_label} afgerond.",
        internship_id=finalized_eval.internship_id,
        link_view="evaluatie",
    )
    db.commit()

    log_event(
        db,
        "evaluation.finalize",
        user=current_user,
        entity_type="internship",
        entity_id=finalized_eval.internship_id,
        detail=f"Evaluatie gefinaliseerd: {finalized_eval.eval_type}",
    )

    return EvaluationWithScoreResponse(
        **EvaluationResponse.model_validate(finalized_eval).model_dump(),
        **score_data,
    )
