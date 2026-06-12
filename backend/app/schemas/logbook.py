"""Logbook schemas."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal
from datetime import date, datetime


class LogbookBase(BaseModel):
    week_number: Optional[int] = Field(
        None, ge=1, description="Internship-relative week number (legacy, optional)"
    )
    entry_date: Optional[date] = Field(
        None, description="Date for this daily logbook entry"
    )
    tasks: Optional[str] = None
    reflection: Optional[str] = None
    issues: Optional[str] = None


class LogbookCreate(LogbookBase):
    pass


class LogbookUpdate(BaseModel):
    tasks: Optional[str] = None
    reflection: Optional[str] = None
    issues: Optional[str] = None
    status: Optional[Literal["draft", "submitted"]] = None
    mentor_validated: Optional[bool] = None
    mentor_feedback: Optional[str] = None
    entry_date: Optional[date] = None


class LogbookResponse(LogbookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    status: str
    mentor_validated: bool
    mentor_feedback: Optional[str] = None
    submitted_at: Optional[datetime] = None
    created_at: datetime


class LogbookDayStatus(BaseModel):
    """Status for a specific day (for displaying all days)"""

    day_offset: int
    entry_date: Optional[date] = None
    logbook_id: Optional[int] = None
    status: str  # missing, draft, submitted
    mentor_validated: bool = False
    mentor_feedback: Optional[str] = None
