"""Internship schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from .user import UserResponse
from .company import CompanyResponse
from .proposal import ProposalResponse
from .agreement import AgreementResponse


class InternshipBase(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class InternshipCreate(BaseModel):
    """Creating an internship starts with a proposal"""
    company_name: str
    company_address: Optional[str] = None
    company_sector: Optional[str] = None
    contact_person: str
    contact_email: str
    start_date: date
    end_date: date
    description: str


class InternshipUpdate(BaseModel):
    teacher_id: Optional[int] = None
    mentor_id: Optional[int] = None
    company_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class InternshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    teacher_id: Optional[int] = None
    mentor_id: Optional[int] = None
    company_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    created_at: datetime

    student: Optional[UserResponse] = None
    teacher: Optional[UserResponse] = None
    mentor: Optional[UserResponse] = None
    company: Optional[CompanyResponse] = None
    proposal: Optional[ProposalResponse] = None
    agreement: Optional[AgreementResponse] = None


class InternshipListResponse(BaseModel):
    """Simplified response for list views — enriched for frontend usability.

    Includes computed fields (proposal_status, agreement_status, agreement_uploaded)
    so the frontend can render meaningful list rows without N+1 detail calls.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    company_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    created_at: datetime

    student: Optional[UserResponse] = None
    company: Optional[CompanyResponse] = None
    teacher: Optional[UserResponse] = None
    mentor: Optional[UserResponse] = None
    proposal_status: Optional[str] = None
    agreement_status: Optional[str] = None
    agreement_uploaded: bool = False
