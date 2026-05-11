from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Competency, CompetencyProfile, EvaluationRule
from app.schemas import (
    CompetencyCreate, CompetencyResponse, CompetencyUpdate,
    CompetencyProfileCreate, CompetencyProfileUpdate, CompetencyProfileResponse,
    CompetencyWithProfileResponse, CompetencyWeightCheck, BulkCompetencyCreate
)
from app.auth import require_admin, get_current_active_user

router = APIRouter(prefix="/competencies", tags=["competencies"])


# ============================================================================
# Competency Profile Endpoints
# ============================================================================

@router.get("/profiles", response_model=List[CompetencyProfileResponse])
def list_profiles(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all competency profiles"""
    query = db.query(CompetencyProfile)
    if active_only:
        query = query.filter(CompetencyProfile.active == True)
    return query.order_by(CompetencyProfile.academic_year.desc()).all()


@router.post("/profiles", response_model=CompetencyProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: CompetencyProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new competency profile (US-25)
    
    Only one profile can be active at a time.
    Creating a new active profile deactivates others.
    """
    profile = CompetencyProfile(
        name=data.name,
        version=data.version,
        academic_year=data.academic_year,
        active=True
    )
    
    # If making this active, deactivate others
    if profile.active:
        db.query(CompetencyProfile).filter(CompetencyProfile.active == True).update({"active": False})
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


@router.get("/profiles/{profile_id}", response_model=CompetencyProfileResponse)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific competency profile"""
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.patch("/profiles/{profile_id}", response_model=CompetencyProfileResponse)
def update_profile(
    profile_id: int,
    update: CompetencyProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a competency profile"""
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    if update.name is not None:
        profile.name = update.name
    if update.version is not None:
        profile.version = update.version
    if update.academic_year is not None:
        profile.academic_year = update.academic_year
    if update.active is not None:
        # If activating, deactivate others
        if update.active and not profile.active:
            db.query(CompetencyProfile).filter(
                CompetencyProfile.active == True,
                CompetencyProfile.id != profile_id
            ).update({"active": False})
        profile.active = update.active
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a competency profile (only if not in use)"""
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check if any competencies are in use in evaluations
    competencies = db.query(Competency).filter(Competency.profile_id == profile_id).all()
    competency_ids = [c.id for c in competencies]
    
    if competency_ids:
        in_use = db.query(EvaluationRule).filter(
            EvaluationRule.competency_id.in_(competency_ids)
        ).first()
        
        if in_use:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete profile: competencies are used in evaluations"
            )
    
    # Delete competencies first
    for comp in competencies:
        db.delete(comp)
    
    db.delete(profile)
    db.commit()
    
    return None


# ============================================================================
# Competency Endpoints
# ============================================================================

@router.get("", response_model=List[CompetencyWithProfileResponse])
def list_competencies(
    profile_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List competencies - optionally filtered by profile"""
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
    current_user: User = Depends(require_admin)
):
    """Create a new competency (US-25)
    
    Each competency must have:
    - name: descriptive name
    - description: detailed description
    - weight: percentage (all active competencies in profile must sum to 100%)
    """
    # Check if profile exists
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == data.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Check if name already exists in this profile
    existing = db.query(Competency).filter(
        Competency.profile_id == data.profile_id,
        Competency.name == data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Competency with this name already exists in the profile"
        )
    
    competency = Competency(
        profile_id=data.profile_id,
        name=data.name,
        description=data.description,
        weight=data.weight,
        active=True
    )
    
    db.add(competency)
    db.commit()
    db.refresh(competency)
    
    return competency


@router.post("/bulk", response_model=List[CompetencyResponse], status_code=status.HTTP_201_CREATED)
def create_competencies_bulk(
    data: BulkCompetencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create multiple competencies at once with weight validation (US-25)
    
    Total weight must equal exactly 100%
    """
    # Check if profile exists
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == data.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Validate total weight
    total_weight = sum(c.weight for c in data.competencies)
    if abs(total_weight - 100.0) > 0.01:  # Allow small floating point differences
        raise HTTPException(
            status_code=400,
            detail=f"Total weight must be exactly 100%, got {total_weight}%"
        )
    
    created = []
    for comp_data in data.competencies:
        # Check for duplicate names
        existing = db.query(Competency).filter(
            Competency.profile_id == data.profile_id,
            Competency.name == comp_data.name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Competency '{comp_data.name}' already exists"
            )
        
        competency = Competency(
            profile_id=data.profile_id,
            name=comp_data.name,
            description=comp_data.description,
            weight=comp_data.weight,
            active=True
        )
        
        db.add(competency)
        created.append(competency)
    
    db.commit()
    
    for comp in created:
        db.refresh(comp)
    
    return created


@router.get("/{competency_id}", response_model=CompetencyWithProfileResponse)
def get_competency(
    competency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific competency"""
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    
    return competency


@router.patch("/{competency_id}", response_model=CompetencyResponse)
def update_competency(
    competency_id: int,
    update: CompetencyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a competency (US-25)
    
    Note: Changing weight may invalidate the 100% total for the profile.
    Use /check-weights to verify after changes.
    """
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    
    if update.name is not None:
        # Check for duplicate names in same profile
        existing = db.query(Competency).filter(
            Competency.profile_id == competency.profile_id,
            Competency.name == update.name,
            Competency.id != competency_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Competency with this name already exists in the profile"
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
    current_user: User = Depends(require_admin)
):
    """Delete a competency (only if not in use)"""
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    
    # Check if in use
    in_use = db.query(EvaluationRule).filter(
        EvaluationRule.competency_id == competency_id
    ).first()
    
    if in_use:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: competency is used in evaluations. Use deactivate instead."
        )
    
    db.delete(competency)
    db.commit()
    
    return None


@router.post("/{competency_id}/deactivate", response_model=CompetencyResponse)
def deactivate_competency(
    competency_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Soft delete by deactivating a competency (US-25)
    
    Wijzigingen gelden enkel voor nieuwe stageperiodes;
    historische evaluaties blijven ongewijzigd.
    """
    competency = db.query(Competency).filter(Competency.id == competency_id).first()
    if not competency:
        raise HTTPException(status_code=404, detail="Competency not found")
    
    competency.active = False
    db.commit()
    db.refresh(competency)
    
    return competency


# ============================================================================
# Weight Validation
# ============================================================================

@router.get("/check-weights", response_model=CompetencyWeightCheck)
def check_weights(
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check if competency weights sum to 100% for a profile (US-25)
    
    Per actief profiel geldt: som van alle competentiegewichten = 100%.
    """
    query = db.query(Competency).filter(Competency.active == True)
    
    if profile_id:
        query = query.filter(Competency.profile_id == profile_id)
        # Check if profile exists
        profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
    else:
        # Use active profile
        active_profile = db.query(CompetencyProfile).filter(CompetencyProfile.active == True).first()
        if active_profile:
            query = query.filter(Competency.profile_id == active_profile.id)
    
    competencies = query.all()
    total_weight = sum(c.weight for c in competencies)
    
    # Valid if total is exactly 100% (with small floating point tolerance)
    is_valid = abs(total_weight - 100.0) < 0.01
    
    return CompetencyWeightCheck(
        total_weight=round(total_weight, 2),
        valid=is_valid,
        competency_count=len(competencies),
        profile_id=profile_id
    )


@router.get("/profiles/{profile_id}/check-weights", response_model=CompetencyWeightCheck)
def check_profile_weights(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check weights for a specific profile"""
    profile = db.query(CompetencyProfile).filter(CompetencyProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    competencies = db.query(Competency).filter(
        Competency.profile_id == profile_id,
        Competency.active == True
    ).all()
    
    total_weight = sum(c.weight for c in competencies)
    is_valid = abs(total_weight - 100.0) < 0.01
    
    return CompetencyWeightCheck(
        total_weight=round(total_weight, 2),
        valid=is_valid,
        competency_count=len(competencies),
        profile_id=profile_id
    )
