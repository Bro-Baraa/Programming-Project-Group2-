"""Competency profile endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user, require_admin
from app.database import get_db
from app.models import Competency, CompetencyProfile, EvaluationRule, User
from app.schemas import (
    CompetencyProfileCreate,
    CompetencyProfileResponse,
    CompetencyProfileUpdate,
)

router = APIRouter()


@router.get("/profiles", response_model=List[CompetencyProfileResponse])
def list_profiles(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all competency profiles."""
    query = db.query(CompetencyProfile)
    if active_only:
        query = query.filter(CompetencyProfile.active == True)
    return query.order_by(CompetencyProfile.academic_year.desc()).all()


@router.post(
    "/profiles",
    response_model=CompetencyProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: CompetencyProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new competency profile."""
    profile = CompetencyProfile(
        name=data.name,
        version=data.version,
        academic_year=data.academic_year,
        active=True,
    )

    if profile.active:
        db.query(CompetencyProfile).filter(CompetencyProfile.active == True).update(
            {"active": False}
        )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profiles/{profile_id}", response_model=CompetencyProfileResponse)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific competency profile."""
    profile = (
        db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.patch("/profiles/{profile_id}", response_model=CompetencyProfileResponse)
def update_profile(
    profile_id: int,
    update: CompetencyProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a competency profile."""
    profile = (
        db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if update.name is not None:
        profile.name = update.name
    if update.version is not None:
        profile.version = update.version
    if update.academic_year is not None:
        profile.academic_year = update.academic_year
    if update.active is not None:
        if update.active and not profile.active:
            db.query(CompetencyProfile).filter(
                CompetencyProfile.active == True,
                CompetencyProfile.id != profile_id,
            ).update({"active": False})
        profile.active = update.active

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a competency profile if its competencies are not used."""
    profile = (
        db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    competencies = (
        db.query(Competency).filter(Competency.profile_id == profile_id).all()
    )
    competency_ids = [competency.id for competency in competencies]

    if competency_ids:
        in_use = (
            db.query(EvaluationRule)
            .filter(EvaluationRule.competency_id.in_(competency_ids))
            .first()
        )
        if in_use:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete profile: competencies are used in evaluations",
            )

    for competency in competencies:
        db.delete(competency)

    db.delete(profile)
    db.commit()
    return None
