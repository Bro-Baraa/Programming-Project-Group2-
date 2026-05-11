"""Dashboard statistics helpers."""

from sqlalchemy.orm import Session

from app.models import Internship, Agreement
from app.schemas import DashboardStats
from .report_common import apply_role_filter


def get_dashboard_stats(db: Session, current_user) -> DashboardStats:
    """Compute the role-scoped internship dashboard summary."""
    base_query = apply_role_filter(db.query(Internship), current_user)

    total = base_query.count()
    pending = base_query.filter(
        Internship.status.in_(["Ingediend", "In Beoordeling"])
    ).count()
    approved = base_query.filter(Internship.status == "Goedgekeurd").count()
    rejected = base_query.filter(Internship.status == "Afgekeurd").count()
    ongoing = base_query.filter(
        Internship.status.in_(["Lopend", "Overeenkomst Ingediend"])
    ).count()

    internship_ids = [internship.id for internship in base_query.all()]
    if internship_ids:
        agreements_received = (
            db.query(Agreement)
            .filter(Agreement.internship_id.in_(internship_ids))
            .count()
        )
        agreements_validated = (
            db.query(Agreement)
            .filter(
                Agreement.internship_id.in_(internship_ids),
                Agreement.status == "Gevalideerd",
            )
            .count()
        )
    else:
        agreements_received = 0
        agreements_validated = 0

    return DashboardStats(
        total_internships=total,
        pending_approval=pending,
        approved=approved,
        rejected=rejected,
        ongoing=ongoing,
        agreements_received=agreements_received,
        agreements_pending=agreements_received - agreements_validated,
    )
