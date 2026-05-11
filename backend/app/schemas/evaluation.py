"""Evaluation schemas."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from .user import UserResponse
from .competency import CompetencyResponse


class EvaluationRuleBase(BaseModel):
    competency_id: int
    score: Optional[int] = Field(None, ge=1, le=5)
    student_description: Optional[str] = None
    evaluator_feedback: Optional[str] = None


class EvaluationRuleCreate(EvaluationRuleBase):
    pass


class EvaluationRuleUpdate(BaseModel):
    score: Optional[int] = Field(None, ge=1, le=5)
    student_description: Optional[str] = None
    evaluator_feedback: Optional[str] = None


class EvaluationRuleResponse(EvaluationRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evaluation_id: int
    competency: Optional[CompetencyResponse] = None


class EvaluationBase(BaseModel):
    eval_type: str  # tussentijds, final
    comments: Optional[str] = None


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationUpdate(BaseModel):
    comments: Optional[str] = None


class EvaluationResponse(EvaluationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    evaluator_id: int
    status: str
    finalized: bool
    created_at: datetime
    finalized_at: Optional[datetime] = None

    evaluator: Optional[UserResponse] = None
    rules: List[EvaluationRuleResponse] = []


class EvaluationFinalizeRequest(BaseModel):
    """Request to finalize an evaluation with scores for all competencies"""
    rules: List[EvaluationRuleBase]
    comments: Optional[str] = None


class EvaluationWithScoreResponse(EvaluationResponse):
    """Evaluation with calculated weighted score"""
    total_weight: float
    achieved_weight: float
    weighted_score: Optional[float] = None  # 0-100 or None if not all scored
