"""Competency item CRUD endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_user, require_admin
from app.database import get_db
from app.models import Competency, CompetencyProfile, EvaluationRule, User
from app.schemas import (
    BulkCompetencyCreate,
    CompetencyCreate,
    CompetencyResponse,
    CompetencyUpdate,
    CompetencyWithProfileResponse,
)

router = APIRouter()


@router.get("", response_model=List[CompetencyWithProfileResponse])
def list_competencies(
    profile_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List competencies with optional filters."""
    query = db.query(Competency)

    if profile_id:
        query = query.filter(Competency.profile_id == profile_id)
    if active_only:
        query = query.filter(Competency.active == True)

    return query.all()


@router.post("", response_model=CompetencyResponse, status_code=status.HTTP_201_CREATED)
def create_competency(
    data: CompetencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a competency under a profile."""
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == data.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    existing = db.query(Competency).filter(
        Competency.profile_id == data.profile_id,
        Competency.name == data.name,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Competency with this name already exists in the profile",
        )

    competency = Competency(
        profile_id=data.profile_id,
        name=data.name,
        description=data.description,
        weight=data.weight,
        active=True,
    )

    db.add(competency)
    db.commit()
    db.refresh(competency)
    return competency


@router.post("/bulk", response_model=List[CompetencyResponse], status_code=status.HTTP_201_CREATED)
def create_competencies_bulk(
    data: BulkCompetencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create multiple competencies at once with total-weight validation."""
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == data.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    total_weight = sum(item.weight for item in data.competencies)
    if abs(total_weight - 100.0) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Total weight must be exactly 100%, got {total_weight}%",
        )

    created = []
    for comp_data in data.competencies:
        existing = db.query(Competency).filter(
            Competency.profile_id == data.profile_id,
            Competency.name == comp_data.name,
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Competency '{comp_data.name}' already exists",
            )

        competency = Competency(
            profile_id=data.profile_id,
            name=comp_data.name,
            description=comp_data.description,
            weight=comp_data.weight,
            active=True,
        )
        db.add(competency)
        created.append(competency)

    db.commit()
    for competency in created:
        db.refresh(competency)

    return created


@router.get("/{competency_id}", response_model=CompetencyWithProfileResponse)
def get_competency(
    competency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific competency."""
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    return competency


@router.patch("/{competency_id}", response_model=CompetencyResponse)
def update_competency(
    competency_id: int,
    update: CompetencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a competency."""
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")

    if update.name is not None:
        existing = db.query(Competency).filter(
            Competency.profile_id == competency.profile_id,
            Competency.name == update.name,
            Competency.id != competency_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Competency with this name already exists in the profile",
            )
        competency.name = update.name

    if update.description is not None:
        competency.description = update.description
    if update.weight is not None:
        competency.weight = update.weight
    if update.active is not None:
        competency.active = update.active

    db.commit()
    db.refresh(competency)
    return competency


@router.delete("/{competency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competency(
    competency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a competency when not used by evaluation rules."""
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")

    in_use = db.query(EvaluationRule).filter(EvaluationRule.competency_id == competency_id).first()
    if in_use:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: competency is used in evaluations. Use deactivate instead.",
        )

    db.delete(competency)
    db.commit()
    return None


@router.post("/{competency_id}/deactivate", response_model=CompetencyResponse)
def deactivate_competency(
    competency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Soft delete a competency by deactivation."""
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")

    competency.active = False
    db.commit()
    db.refresh(competency)
    return competency
