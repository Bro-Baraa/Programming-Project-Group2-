from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Company, User
from app.schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from app.auth import get_current_active_user, require_admin, require_any_staff

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=List[CompanyResponse])
def list_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all companies - accessible to all authenticated users"""
    return db.query(Company).all()


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    """Create a new company - staff only"""
    # If mentor_id provided, validate it exists and has mentor role
    if data.mentor_id:
        mentor = db.query(User).filter(User.id == data.mentor_id).first()
        if not mentor:
            raise HTTPException(status_code=404, detail="Mentor not found")
        if mentor.role != "mentor":
            raise HTTPException(status_code=400, detail="User is not a mentor")
    
    company = Company(
        name=data.name,
        address=data.address,
        sector=data.sector,
        contact_person=data.contact_person,
        contact_email=data.contact_email,
        mentor_id=data.mentor_id
    )
    
    db.add(company)
    db.commit()
    db.refresh(company)
    
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific company by ID"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    update: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_staff)
):
    """Update a company - staff only"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # If changing mentor_id, validate it
    if update.mentor_id is not None:
        mentor = db.query(User).filter(User.id == update.mentor_id).first()
        if not mentor:
            raise HTTPException(status_code=404, detail="Mentor not found")
        if mentor.role != "mentor":
            raise HTTPException(status_code=400, detail="User is not a mentor")
    
    if update.name is not None:
        company.name = update.name
    if update.address is not None:
        company.address = update.address
    if update.sector is not None:
        company.sector = update.sector
    if update.contact_person is not None:
        company.contact_person = update.contact_person
    if update.contact_email is not None:
        company.contact_email = update.contact_email
    if update.mentor_id is not None:
        company.mentor_id = update.mentor_id
    
    db.commit()
    db.refresh(company)
    
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a company - admin only"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if company has internships
    if company.internships:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete company with associated internships"
        )
    
    db.delete(company)
    db.commit()
    
    return None
