"""Proposal schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ProposalBase(BaseModel):
    description: str


class ProposalCreate(ProposalBase):
    pass


class ProposalUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    feedback: Optional[str] = None


class ProposalResponse(ProposalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    status: str
    feedback: Optional[str] = None
    submitted_at: datetime
