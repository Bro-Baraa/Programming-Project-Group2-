"""Evaluation scoring helpers."""
from sqlalchemy.orm import Session, joinedload

from app.models import Evaluation, EvaluationRule


def calculate_evaluation_score(db: Session, evaluation: Evaluation) -> dict:
    """Calculate the weighted score for an evaluation."""
    rules = (
        db.query(EvaluationRule)
        .options(joinedload(EvaluationRule.competency))
        .filter(EvaluationRule.evaluation_id == evaluation.id)
        .all()
    )

    if not rules:
        return {
            "total_weight": 0,
            "achieved_weight": 0,
            "weighted_score": None,
        }

    total_weight = 0
    achieved_weight = 0
    all_scored = True

    for rule in rules:
        competency = rule.competency
        if competency:
            weight = competency.weight
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
