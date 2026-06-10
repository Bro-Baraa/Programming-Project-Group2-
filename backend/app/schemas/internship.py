from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime, date
from .user import UserResponse
from .company import CompanyResponse
from .proposal import ProposalResponse
from .agreement import AgreementResponse


class InternshipBase(BaseModel):
    start_date: Optional[date] = Field(
        None, description="Startdatum van de stageperiode"
    )
    end_date: Optional[date] = Field(None, description="Einddatum van de stageperiode")


class InternshipCreate(BaseModel):
    """Creating an internship starts with a proposal"""

    company_name: str = Field(..., description="Naam van het stagebedrijf")
    company_address: Optional[str] = Field(
        None, description="Adres van het stagebedrijf"
    )
    company_sector: Optional[str] = Field(
        None, description="Sector waarin het bedrijf actief is"
    )
    contact_person: str = Field(
        ..., description="Naam van de contactpersoon/begeleider bij het bedrijf"
    )
    contact_email: str = Field(
        ..., description="E-mailadres van de contactpersoon/begeleider"
    )
    start_date: date = Field(..., description="Startdatum van de stage")
    end_date: date = Field(..., description="Einddatum van de stage")
    description: str = Field(
        ..., description="Gedetailleerde taakomschrijving van de stageopdracht"
    )
    teacher_id: Optional[int] = Field(
        None, description="ID van de toegewezen EhB-docent"
    )
    mentor_id: Optional[int] = Field(
        None, description="ID van de stagementor van het bedrijf"
    )


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
    competency_profile_id: Optional[int] = None
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
