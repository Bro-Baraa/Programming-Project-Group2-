"""API routers package."""

from .auth import router as auth_router
from .companies import router as companies_router
from .internships import router as internships_router
from .proposals import router as proposals_router
from .agreements import router as agreements_router
from .logbooks import router as logbooks_router
from .evaluations import router as evaluations_router
from .feedback import router as feedback_router
from .reports import router as reports_router
from .competencies import router as competencies_router
from .users import router as users_router
from .me import router as me_router
from .notifications import router as notifications_router
from .audit import router as audit_router

# Re-export for convenience
auth = auth_router
companies = companies_router
internships = internships_router
proposals = proposals_router
agreements = agreements_router
logbooks = logbooks_router
evaluations = evaluations_router
feedback = feedback_router
reports = reports_router
competencies = competencies_router
users = users_router
me = me_router
notifications = notifications_router
audit = audit_router
