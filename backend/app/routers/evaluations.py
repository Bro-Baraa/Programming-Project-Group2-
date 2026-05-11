"""Evaluation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Evaluation, User
from app.schemas import (
    EvaluationResponse,
    EvaluationCreate,
    EvaluationRuleResponse,
    EvaluationRuleUpdate,
    EvaluationWithScoreResponse,
)
from app.auth import get_current_active_user, require_teacher, require_any_staff
from app.services.evaluations import (
    create_evaluation as create_evaluation_svc,
    get_evaluation_with_score,
    list_evaluations as list_evaluations_svc,
    update_evaluation_rule as update_evaluation_rule_svc,
    finalize_evaluation as finalize_evaluation_svc,
)

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
    current_user: User = Depends(require_teacher),
):
    """US-17, US-18: Teacher creates an evaluation (tussentijds or final)"""
    return create_evaluation_svc(db, current_user, internship_id, data)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationWithScoreResponse)
def get_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get evaluation with calculated score"""
    return get_evaluation_with_score(db, current_user, evaluation_id)


@router.patch(
    "/evaluations/{evaluation_id}/rules/{rule_id}", response_model=EvaluationRuleResponse
)
def update_evaluation_rule(
    evaluation_id: int,
    rule_id: int,
    update: EvaluationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff),
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
    """US-18: Finalize an evaluation - cannot be modified after"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # finalize_evaluation_svc returns (Evaluation, dict) tuple
    finalized_eval, score_data = finalize_evaluation_svc(db, evaluation, current_user)

    return EvaluationWithScoreResponse(
        **EvaluationResponse.model_validate(finalized_eval).model_dump(),
        **score_data,
    )
