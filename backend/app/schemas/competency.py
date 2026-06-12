"""Competency schemas."""

from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime


def _check_weight(v: float | None) -> float | None:
    if v is None:
        return v
    if v <= 0:
        raise ValueError("Weight must be greater than 0")
    if v > 100:
        raise ValueError("Weight cannot exceed 100")
    return v


class CompetencyProfileBase(BaseModel):
    name: str
    version: str
    academic_year: str


class CompetencyProfileCreate(CompetencyProfileBase):
    active: bool = True


class CompetencyProfileUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    academic_year: Optional[str] = None
    active: Optional[bool] = None


class CompetencyProfileResponse(CompetencyProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    active: bool
    created_at: datetime


class CompetencyBase(BaseModel):
    name: str
    description: Optional[str] = None
    weight: float


class CompetencyCreate(CompetencyBase):
    profile_id: int

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        return _check_weight(v)


class CompetencyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[float] = None
    active: Optional[bool] = None

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        return _check_weight(v)


class CompetencyResponse(CompetencyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    active: bool
    created_at: datetime


class CompetencyWithProfileResponse(CompetencyResponse):
    profile: Optional[CompetencyProfileResponse] = None


class CompetencyWeightCheck(BaseModel):
    """Result of checking competency weights"""

    total_weight: float
    valid: bool
    competency_count: int
    profile_id: Optional[int] = None


class BulkCompetencyCreate(BaseModel):
    """Create multiple competencies at once for a profile"""

    profile_id: int
    competencies: List[CompetencyBase]

    @field_validator("competencies")
    @classmethod
    def validate_total_weight(cls, competencies):
        total = sum(c.weight for c in competencies)
        if abs(total - 100) > 0.01:
            raise ValueError(f"Total weight must be exactly 100%, got {total}%")
        return competencies
