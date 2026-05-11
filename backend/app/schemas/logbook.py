"""Logbook schemas."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class LogbookBase(BaseModel):
    week_number: int = Field(ge=1, description="Internship-relative week number (week 1, 2, 3, ...)")
    tasks: Optional[str] = None
    reflection: Optional[str] = None
    issues: Optional[str] = None


class LogbookCreate(LogbookBase):
    pass


class LogbookUpdate(BaseModel):
    tasks: Optional[str] = None
    reflection: Optional[str] = None
    issues: Optional[str] = None
    status: Optional[str] = None  # draft, submitted
    mentor_validated: Optional[bool] = None


class LogbookResponse(LogbookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    status: str
    mentor_validated: bool
    submitted_at: Optional[datetime] = None
    created_at: datetime


class LogbookWeekStatus(BaseModel):
    """Status for a specific week (for displaying all weeks)"""
    week_number: int
    logbook_id: Optional[int] = None
    status: str  # missing, draft, submitted
    mentor_validated: bool = False
