"""Pydantic schemas for request/response validation.

This package provides schemas organized by domain:
- user: User-related schemas
- company: Company-related schemas
- proposal: Proposal-related schemas
- agreement: Agreement-related schemas
- internship: Internship-related schemas
- logbook: Logbook-related schemas
- competency: Competency profile schemas
- evaluation: Evaluation schemas
- feedback: Feedback schemas
- report: Dashboard and reporting schemas
"""

# Re-export all schemas for backward compatibility
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    Token,
)
from .company import (
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
)
from .proposal import (
    ProposalBase,
    ProposalCreate,
    ProposalUpdate,
    ProposalResponse,
)
from .agreement import (
    AgreementBase,
    AgreementUpdate,
    AgreementResponse,
)
from .internship import (
    InternshipBase,
    InternshipCreate,
    InternshipUpdate,
    InternshipResponse,
    InternshipListResponse,
)
from .logbook import (
    LogbookBase,
    LogbookCreate,
    LogbookUpdate,
    LogbookResponse,
    LogbookWeekStatus,
)
from .competency import (
    CompetencyProfileBase,
    CompetencyProfileCreate,
    CompetencyProfileUpdate,
    CompetencyProfileResponse,
    CompetencyBase,
    CompetencyCreate,
    CompetencyUpdate,
    CompetencyResponse,
    CompetencyWithProfileResponse,
    CompetencyWeightCheck,
    BulkCompetencyCreate,
)
from .evaluation import (
    EvaluationRuleBase,
    EvaluationRuleCreate,
    EvaluationRuleUpdate,
    EvaluationRuleResponse,
    EvaluationBase,
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationResponse,
    EvaluationFinalizeRequest,
    EvaluationWithScoreResponse,
)
from .feedback import (
    FeedbackBase,
    FeedbackCreate,
    FeedbackResponse,
)
from .report import (
    DashboardStats,
    AgreementStatusItem,
    FinalReportItem,
)
from .dashboard import (
    InternshipDashboardItem,
    UserDashboardStats,
    DashboardAlert,
    MeDashboardResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "Token",
    # Company
    "CompanyBase",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    # Proposal
    "ProposalBase",
    "ProposalCreate",
    "ProposalUpdate",
    "ProposalResponse",
    # Agreement
    "AgreementBase",
    "AgreementUpdate",
    "AgreementResponse",
    # Internship
    "InternshipBase",
    "InternshipCreate",
    "InternshipUpdate",
    "InternshipResponse",
    "InternshipListResponse",
    # Logbook
    "LogbookBase",
    "LogbookCreate",
    "LogbookUpdate",
    "LogbookResponse",
    "LogbookWeekStatus",
    # Competency
    "CompetencyProfileBase",
    "CompetencyProfileCreate",
    "CompetencyProfileUpdate",
    "CompetencyProfileResponse",
    "CompetencyBase",
    "CompetencyCreate",
    "CompetencyUpdate",
    "CompetencyResponse",
    "CompetencyWithProfileResponse",
    "CompetencyWeightCheck",
    "BulkCompetencyCreate",
    # Evaluation
    "EvaluationRuleBase",
    "EvaluationRuleCreate",
    "EvaluationRuleUpdate",
    "EvaluationRuleResponse",
    "EvaluationBase",
    "EvaluationCreate",
    "EvaluationUpdate",
    "EvaluationResponse",
    "EvaluationFinalizeRequest",
    "EvaluationWithScoreResponse",
    # Feedback
    "FeedbackBase",
    "FeedbackCreate",
    "FeedbackResponse",
    # Report
    "DashboardStats",
    "AgreementStatusItem",
    "FinalReportItem",
    # Dashboard
    "InternshipDashboardItem",
    "UserDashboardStats",
    "DashboardAlert",
    "MeDashboardResponse",
]
