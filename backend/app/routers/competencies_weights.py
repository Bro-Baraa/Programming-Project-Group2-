"""Competency weight validation endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.database import get_db
from app.models import Competency, CompetencyProfile, User
from app.schemas import CompetencyWeightCheck

router = APIRouter()


def _calculate_profile_weight_status(
    db: Session, profile_id: int
) -> CompetencyWeightCheck:
    """Calculate active competency weight status for a profile."""
    profile = (
        db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    competencies = (
        db.query(Competency)
        .filter(
            Competency.profile_id == profile_id,
            Competency.active == True,
        )
        .all()
    )

    total_weight = sum(competency.weight for competency in competencies)
    return CompetencyWeightCheck(
        total_weight=round(total_weight, 2),
        valid=abs(total_weight - 100.0) < 0.01,
        competency_count=len(competencies),
        profile_id=profile_id,
    )


@router.get("/check-weights", response_model=CompetencyWeightCheck)
def check_weights(
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Check if active competency weights sum to 100%."""
    if profile_id:
        return _calculate_profile_weight_status(db, profile_id)

    active_profile = (
        db.query(CompetencyProfile).filter(CompetencyProfile.active == True).first()
    )
    if not active_profile:
        return CompetencyWeightCheck(
            total_weight=0,
            valid=False,
            competency_count=0,
            profile_id=None,
        )

    return _calculate_profile_weight_status(db, active_profile.id)


@router.get(
    "/profiles/{profile_id}/check-weights", response_model=CompetencyWeightCheck
)
def check_profile_weights(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Check active competency weights for one profile."""
    return _calculate_profile_weight_status(db, profile_id)
