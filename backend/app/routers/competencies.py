from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Competency, User
from app.schemas import CompetencyCreate, CompetencyResponse, CompetencyUpdate
from app.auth import require_admin, get_current_active_user

router = APIRouter(prefix="/competencies", tags=["competencies"])


@router.get("", response_model=List[CompetencyResponse])
def list_competencies(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Competency)
    if active_only:
        query = query.filter(Competency.active == True)
    return query.all()


@router.post("", response_model=CompetencyResponse)
def create_competency(
    data: CompetencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    # Check if name already exists
    existing = db.query(Competency).filter(Competency.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Competency with this name already exists")
    
    competency = Competency(
        name=data.name,
        weight=data.weight,
        active=True
    )
    
    db.add(competency)
    db.commit()
    db.refresh(competency)
    
    return competency


@router.patch("/{competency_id}", response_model=CompetencyResponse)
def update_competency(
    competency_id: int,
    update: CompetencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    
    if update.name is not None:
        competency.name = update.name
    if update.weight is not None:
        competency.weight = update.weight
    if update.active is not None:
        competency.active = update.active
    
    db.commit()
    db.refresh(competency)
    
    return competency


@router.delete("/{competency_id}")
def delete_competency(
    competency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    
    # Soft delete by marking inactive
    competency.active = False
    db.commit()
    
    return {"message": "Competency deactivated successfully"}


@router.get("/check-weights")
def check_weights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if competency weights sum to 100%"""
    competencies = db.query(Competency).filter(Competency.active == True).all()
    total_weight = sum(c.weight for c in competencies)
    
    return {
        "total_weight": total_weight,
        "valid": total_weight == 100,
        "competency_count": len(competencies)
    }