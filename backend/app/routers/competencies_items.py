"""Competency item CRUD endpoints."""

from threading import Lock
from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

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
from app.dependencies import pagination
from app.services.audit import log_event

router = APIRouter()

_competency_create_lock = Lock()


@router.get("", response_model=List[CompetencyWithProfileResponse])
def list_competencies(
    response: Response,
    profile_id: Optional[int] = None,
    active_only: bool = True,
    search: Annotated[
        Optional[str],
        Query(min_length=1, max_length=100, description="Search competency name"),
    ] = None,
    pag: Annotated[dict, Depends(pagination)] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List competencies with optional filters, search, and pagination.

    Query params:
    - profile_id: filter by profile
    - active_only: exclude deactivated (default true)
    - search: keyword search on competency name
    - skip / limit: pagination
    """
    query = db.query(Competency)

    if profile_id:
        query = query.filter(Competency.profile_id == profile_id)
    if active_only:
        query = query.filter(Competency.active == True)

    if search:
        query = query.filter(Competency.name.ilike(f"%{search}%"))

    # Count total
    total_count = query.with_entities(func.count(Competency.id)).scalar()
    response.headers["X-Total-Count"] = str(total_count)

    # Pagination
    skip = pag.get("skip", 0) if pag else 0
    limit = pag.get("limit", 50) if pag else 50
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=CompetencyResponse, status_code=status.HTTP_201_CREATED)
def create_competency(
    data: CompetencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a competency under a profile."""
    profile = (
        db.query(CompetencyProfile)
        .filter(CompetencyProfile.id == data.profile_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Competency name is required")

    with _competency_create_lock:
        existing = (
            db.query(Competency)
            .filter(
                Competency.profile_id == data.profile_id,
                Competency.name == name,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Competency with this name already exists in the profile",
            )

        competency = Competency(
            profile_id=data.profile_id,
            name=name,
            description=data.description,
            weight=data.weight,
            active=True,
        )

        db.add(competency)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Competency with this name already exists in the profile",
            )
        db.refresh(competency)
    log_event(
        db,
        "competency.create",
        user=current_user,
        entity_type="competency",
        entity_id=competency.id,
        detail=f"Competentie aangemaakt: {competency.name}",
    )
    return competency


@router.post(
    "/bulk",
    response_model=List[CompetencyResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_competencies_bulk(
    data: BulkCompetencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create multiple competencies at once with total-weight validation."""
    profile = (
        db.query(CompetencyProfile)
        .filter(CompetencyProfile.id == data.profile_id)
        .first()
    )
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
        existing = (
            db.query(Competency)
            .filter(
                Competency.profile_id == data.profile_id,
                Competency.name == comp_data.name,
            )
            .first()
        )
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
        existing = (
            db.query(Competency)
            .filter(
                Competency.profile_id == competency.profile_id,
                Competency.name == update.name,
                Competency.id != competency_id,
            )
            .first()
        )
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
    log_event(
        db,
        "competency.update",
        user=current_user,
        entity_type="competency",
        entity_id=competency.id,
        detail=f"Competentie gewijzigd: {competency.name}",
    )
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

    in_use = (
        db.query(EvaluationRule)
        .filter(EvaluationRule.competency_id == competency_id)
        .first()
    )
    if in_use:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: competency is used in evaluations. Use deactivate instead.",
        )

    db.delete(competency)
    db.commit()
    log_event(
        db,
        "competency.delete",
        user=current_user,
        entity_type="competency",
        entity_id=competency_id,
        detail=f"Competentie verwijderd: {competency.name}",
    )
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
    log_event(
        db,
        "competency.deactivate",
        user=current_user,
        entity_type="competency",
        entity_id=competency_id,
        detail=f"Competentie gedeactiveerd: {competency.name}",
    )
    return competency
