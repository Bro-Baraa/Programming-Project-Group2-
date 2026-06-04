"""Proposal schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date


class ProposalBase(BaseModel):
    description: str


class ProposalCreate(ProposalBase):
    pass


class ProposalUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    feedback: Optional[str] = None
    teacher_id: Optional[int] = None


class ProposalResponse(ProposalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    status: str
    feedback: Optional[str] = None
    submitted_at: datetime
    revision_count: int = 0
    resubmitted_at: Optional[datetime] = None


class EditProposalRequest(BaseModel):
    """Student edits proposal while status is still 'Ingediend'.
    All fields are optional; omitted fields keep current values."""
    description: Optional[str] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_sector: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ResubmitRequest(BaseModel):
    """Student resubmits proposal after changes requested.
    All fields are optional except new_description; omitted fields keep current values."""
    new_description: str
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_sector: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
