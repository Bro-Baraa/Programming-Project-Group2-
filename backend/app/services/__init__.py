"""Services package for business logic."""

from .common import (
    can_access_internship,
    ensure_internship_access,
    get_active_competency_profile,
)
from .lifecycle import (
    InternshipLifecycle,
    LifecycleConfig,
    NewInternship,
    ReviewDecision,
    AgreementUpload,
)
from .logbooks import (
    create_logbook,
    update_logbook,
)
from .evaluations import (
    calculate_evaluation_score,
    create_evaluation,
    finalize_evaluation,
    get_evaluation_with_score,
    list_evaluations,
    update_evaluation_rule,
)
from .feedback import (
    create_feedback,
    list_feedback,
)
from .reports import (
    get_agreement_status_report,
    get_dashboard_stats,
    get_final_report,
)

__all__ = [
    # Common
    "can_access_internship",
    "ensure_internship_access",
    "get_active_competency_profile",
    # Lifecycle
    "InternshipLifecycle",
    "LifecycleConfig",
    "NewInternship",
    "ReviewDecision",
    "AgreementUpload",
    # Logbooks
    "create_logbook",
    "update_logbook",
    # Evaluations
    "calculate_evaluation_score",
    "create_evaluation",
    "finalize_evaluation",
    "get_evaluation_with_score",
    "list_evaluations",
    "update_evaluation_rule",
    # Feedback
    "create_feedback",
    "list_feedback",
    # Reports
    "get_agreement_status_report",
    "get_dashboard_stats",
    "get_final_report",
]
