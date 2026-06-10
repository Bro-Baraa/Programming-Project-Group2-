"""Company schemas."""

from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from .user import UserResponse


class CompanyBase(BaseModel):
    name: str
    address: Optional[str] = None
    sector: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None


class CompanyCreate(CompanyBase):
    mentor_id: Optional[int] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    sector: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    mentor_id: Optional[int] = None


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mentor_id: Optional[int] = None
    created_at: datetime
    mentor: Optional[UserResponse] = None
