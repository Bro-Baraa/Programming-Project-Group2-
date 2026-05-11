from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator
from typing import Optional, List
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


# Company (Bedrijf) schemas
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


# Proposal (Stagevoorstel) schemas
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


# Agreement (Overeenkomst) schemas
class AgreementBase(BaseModel):
    insurance_verified: bool = False
    status: str = "Niet Ingediend"


class AgreementUpdate(BaseModel):
    insurance_verified: Optional[bool] = None
    status: Optional[str] = None


class AgreementResponse(AgreementBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    internship_id: int
    file_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None


# Document schemas
class DocumentBase(BaseModel):
    doc_type: str


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    internship_id: int
    file_path: str
    uploaded_at: datetime


# Internship schemas
class InternshipBase(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class InternshipCreate(BaseModel):
    """Creating an internship starts with a proposal"""
    company_name: str
    company_address: Optional[str] = None
    company_sector: Optional[str] = None
    contact_person: str
    contact_email: EmailStr
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


class InternshipUpdateStatus(BaseModel):
    status: str
    feedback: Optional[str] = None


class InternshipListResponse(BaseModel):
    """Simplified response for list views"""
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


# Logbook schemas
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


# Competency Profile schemas
class CompetencyProfileBase(BaseModel):
    name: str
    version: str
    academic_year: str


class CompetencyProfileCreate(CompetencyProfileBase):
    pass


class CompetencyProfileUpdate(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    academic_year: Optional[str] = None
    active: Optional[bool] = None


class CompetencyProfileResponse(CompetencyProfileBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    active: bool
    created_at: datetime


# Competency schemas
class CompetencyBase(BaseModel):
    name: str
    description: Optional[str] = None
    weight: float


class CompetencyCreate(CompetencyBase):
    profile_id: int

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
    description: Optional[str] = None
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
    profile_id: int
    active: bool
    created_at: datetime


class CompetencyWithProfileResponse(CompetencyResponse):
    profile: Optional[CompetencyProfileResponse] = None


# Evaluation Rule schemas
class EvaluationRuleBase(BaseModel):
    competency_id: int
    score: Optional[int] = Field(None, ge=1, le=5)
    student_description: Optional[str] = None
    evaluator_feedback: Optional[str] = None


class EvaluationRuleCreate(EvaluationRuleBase):
    pass


class EvaluationRuleUpdate(BaseModel):
    score: Optional[int] = Field(None, ge=1, le=5)
    student_description: Optional[str] = None
    evaluator_feedback: Optional[str] = None


class EvaluationRuleResponse(EvaluationRuleBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    evaluation_id: int
    competency: Optional[CompetencyResponse] = None


# Evaluation schemas
class EvaluationBase(BaseModel):
    eval_type: str  # tussentijds, final
    comments: Optional[str] = None


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationUpdate(BaseModel):
    comments: Optional[str] = None


class EvaluationResponse(EvaluationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    internship_id: int
    evaluator_id: int
    status: str
    finalized: bool
    created_at: datetime
    finalized_at: Optional[datetime] = None
    
    evaluator: Optional[UserResponse] = None
    rules: List[EvaluationRuleResponse] = []


class EvaluationFinalizeRequest(BaseModel):
    """Request to finalize an evaluation with scores for all competencies"""
    rules: List[EvaluationRuleBase]
    comments: Optional[str] = None


class EvaluationWithScoreResponse(EvaluationResponse):
    """Evaluation with calculated weighted score"""
    total_weight: float
    achieved_weight: float
    weighted_score: Optional[float] = None  # 0-100 or None if not all scored


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


# Dashboard and reporting schemas
class DashboardStats(BaseModel):
    total_internships: int
    pending_approval: int
    approved: int
    rejected: int
    ongoing: int
    agreements_received: int
    agreements_pending: int


class AgreementStatusItem(BaseModel):
    """For US-26: admin overview of agreement status"""
    internship_id: int
    student: UserResponse
    status: str
    agreement_status: str
    uploaded_at: Optional[datetime] = None


class FinalReportItem(BaseModel):
    """For US-19: final report per student"""
    internship_id: int
    student: UserResponse
    company_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Proposal info
    proposal_status: str
    proposal_submitted_at: Optional[datetime] = None
    
    # Agreement info
    agreement_status: str
    agreement_uploaded_at: Optional[datetime] = None
    
    # Logbook summary
    total_weeks: int
    submitted_logbooks: int
    missing_logbooks: int
    
    # Evaluations
    final_evaluation: Optional[EvaluationWithScoreResponse] = None
    weighted_final_score: Optional[float] = None


class CompetencyWeightCheck(BaseModel):
    """Result of checking competency weights"""
    total_weight: float
    valid: bool
    competency_count: int
    profile_id: Optional[int] = None


class BulkCompetencyCreate(BaseModel):
    """Create multiple competencies at once for a profile"""
    profile_id: int
    competencies: List[CompetencyBase]
    
    @field_validator('competencies')
    @classmethod
    def validate_total_weight(cls, competencies):
        total = sum(c.weight for c in competencies)
        if total != 100:
            raise ValueError(f'Total weight must be exactly 100%, got {total}%')
        return competencies
