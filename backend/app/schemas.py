from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional, Dict
from datetime import datetime, date


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Internship schemas
class InternshipBase(BaseModel):
    company_name: str
    contact_person: str
    contact_email: EmailStr
    start_date: date
    end_date: date
    description: str


class InternshipCreate(InternshipBase):
    pass


class InternshipUpdateStatus(BaseModel):
    status: str
    feedback: Optional[str] = None


class InternshipResponse(InternshipBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    student_id: int
    status: str
    agreement_uploaded: bool
    agreement_filename: Optional[str] = None
    committee_feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    student: Optional[UserResponse] = None


# Logbook schemas
class LogbookBase(BaseModel):
    week_number: int
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


# Competency schemas
class CompetencyBase(BaseModel):
    name: str
    weight: float


class CompetencyCreate(CompetencyBase):
    @field_validator('weight')
    @classmethod
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError('Weight must be greater than 0')
        if v > 100:
            raise ValueError('Weight cannot exceed 100')
        return v


class CompetencyUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    active: Optional[bool] = None
    
    @field_validator('weight')
    @classmethod
    def validate_weight(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError('Weight must be greater than 0')
            if v > 100:
                raise ValueError('Weight cannot exceed 100')
        return v


class CompetencyResponse(CompetencyBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    active: bool
    created_at: datetime


class CompetencyScore(BaseModel):
    competency_id: int
    score: int = Field(ge=1, le=5, description="Score must be between 1 and 5")


# Evaluation schemas
class EvaluationBase(BaseModel):
    type: str  # tussentijds, final
    scores: Dict[str, int]  # competency_id -> score (keys as strings for JSON)
    comments: Optional[str] = None
    
    @field_validator('scores', mode='before')
    @classmethod
    def parse_scores(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v) if v else {}
        return v if v is not None else {}


class EvaluationCreate(BaseModel):
    type: str
    comments: Optional[str] = None


class EvaluationUpdate(BaseModel):
    scores: Optional[Dict[str, int]] = None  # competency_id -> score
    comments: Optional[str] = None


class EvaluationFinalize(BaseModel):
    scores: Dict[str, int]  # competency_id -> score (required for finalization)


class EvaluationResponse(EvaluationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    internship_id: int
    evaluator_id: int
    finalized: bool
    created_at: datetime
    finalized_at: Optional[datetime] = None
    
    evaluator: Optional[UserResponse] = None


# Feedback schemas
class FeedbackBase(BaseModel):
    message: str


class FeedbackCreate(FeedbackBase):
    to_user_id: int


class FeedbackResponse(FeedbackBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    internship_id: int
    from_user_id: int
    to_user_id: int
    created_at: datetime
    
    from_user: Optional[UserResponse] = None
    to_user: Optional[UserResponse] = None


# Dashboard stats
class DashboardStats(BaseModel):
    total_internships: int
    pending_approval: int
    approved: int
    rejected: int
    ongoing: int
    agreements_received: int
    agreements_pending: int


