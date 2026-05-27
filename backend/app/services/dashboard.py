"""Dashboard aggregation service.

Builds the /me/dashboard response by gathering all data a user needs
for their primary view in a single, efficient query pass.
"""

from datetime import datetime, UTC
from typing import List

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import (
    Feedback,
    Internship,
    Logbook,
    Evaluation,
    User,
)
from app.schemas import (
    InternshipDashboardItem,
    UserDashboardStats,
    DashboardAlert,
    MeDashboardResponse,
    UserResponse,
    InternshipListResponse,
    FeedbackResponse,
)
from app.services.common import can_access_internship


def _build_internship_dashboard_item(
    internship: Internship,
    logbooks: List[Logbook],
    evaluations: List[Evaluation],
    feedbacks: List[Feedback],
) -> InternshipDashboardItem:
    """Construct a rich dashboard summary for one internship."""

    # Logbook math
    total_weeks = 0
    logbooks_submitted = 0
    logbooks_draft = 0
    next_due_week = None

    if internship.start_date and internship.end_date:
        total_days = (internship.end_date - internship.start_date).days
        total_weeks = max(1, (total_days // 7) + 1)

    existing_weeks = {lb.week_number for lb in logbooks}
    logbooks_submitted = sum(1 for lb in logbooks if lb.status == "submitted")
    logbooks_draft = sum(1 for lb in logbooks if lb.status == "draft")
    logbooks_missing = total_weeks - len(existing_weeks)

    # Next due week = first missing week
    if total_weeks > 0:
        for week in range(1, total_weeks + 1):
            if week not in existing_weeks:
                next_due_week = week
                break

    # Evaluation summary
    evaluations_count = len(evaluations)
    evaluations_finalized = sum(1 for ev in evaluations if ev.finalized)
    latest_eval = None
    if evaluations:
        latest_eval = max(evaluations, key=lambda ev: ev.created_at)

    # Recent feedback (last 3, newest first)
    recent_feedback = sorted(
        feedbacks,
        key=lambda f: f.created_at,
        reverse=True,
    )[:3]

    return InternshipDashboardItem(
        internship=InternshipListResponse.model_validate(internship),
        proposal_status=internship.proposal.status if internship.proposal else None,
        agreement_status=internship.agreement.status if internship.agreement else None,
        agreement_uploaded=internship.agreement is not None,
        total_weeks=total_weeks,
        logbooks_submitted=logbooks_submitted,
        logbooks_missing=max(0, logbooks_missing),
        logbooks_draft=logbooks_draft,
        next_due_week=next_due_week,
        evaluations_count=evaluations_count,
        evaluations_finalized=evaluations_finalized,
        latest_evaluation_status=latest_eval.status if latest_eval else None,
        recent_feedback=[FeedbackResponse.model_validate(f) for f in recent_feedback],
    )


def _build_alerts(
    user: User,
    internship_items: List[InternshipDashboardItem],
) -> List[DashboardAlert]:
    """Generate actionable alerts based on the user's data."""
    alerts: List[DashboardAlert] = []

    for item in internship_items:
        i = item.internship
        intern_id = i.id

        # Student-specific alerts
        if user.role == "student":
            if i.status == "Aanpassingen Vereist":
                alerts.append(DashboardAlert(
                    severity="warning",
                    message="Je stagevoorstel heeft aanpassingen nodig. Bekijk de feedback en dien opnieuw in.",
                    action_url="?view=voorstel",
                    entity_type="internship",
                    entity_id=intern_id,
                ))
            if i.status == "Goedgekeurd" and not item.agreement_uploaded:
                alerts.append(DashboardAlert(
                    severity="warning",
                    message="Je stage is goedgekeurd. Upload je ondertekende overeenkomst.",
                    action_url="?view=overeenkomst",
                    entity_type="internship",
                    entity_id=intern_id,
                ))
            if item.next_due_week and i.status == "Lopend":
                alerts.append(DashboardAlert(
                    severity="info",
                    message=f"Week {item.next_due_week} logboek nog niet ingevuld.",
                    action_url="?view=logboek",
                    entity_type="logbook",
                    entity_id=intern_id,
                ))

        # Teacher-specific alerts
        if user.role == "teacher":
            if item.logbooks_submitted > 0:
                pending_validation = item.logbooks_submitted - item.evaluations_count
                if pending_validation > 0:
                    alerts.append(DashboardAlert(
                        severity="info",
                        message=f"{pending_validation} logboek(en) in afwachting van evaluatie bij {i.student.first_name} {i.student.last_name}.",
                        entity_type="internship",
                        entity_id=intern_id,
                    ))

        # Committee-specific alerts
        if user.role in ("committee", "admin"):
            if i.status == "In Beoordeling":
                alerts.append(DashboardAlert(
                    severity="warning",
                    message=f"Voorstel van {i.student.first_name} {i.student.last_name} wacht op beoordeling.",
                    action_url="?view=voorstellen",
                    entity_type="internship",
                    entity_id=intern_id,
                ))
            if item.agreement_status == "Ingediend":
                alerts.append(DashboardAlert(
                    severity="info",
                    message=f"Overeenkomst van {i.student.first_name} {i.student.last_name} wacht op validatie.",
                    action_url="?view=overzicht",
                    entity_type="internship",
                    entity_id=intern_id,
                ))

        # Mentor-specific alerts
        if user.role == "mentor" and item.logbooks_submitted > 0:
            alerts.append(DashboardAlert(
                severity="info",
                message=f"Nieuwe logboeken ingediend door {i.student.first_name} {i.student.last_name}.",
                action_url="?view=validatie",
                entity_type="internship",
                entity_id=intern_id,
            ))

    return sorted(alerts, key=lambda a: {"error": 0, "warning": 1, "info": 2}[a.severity])


def _build_stats(
    user: User,
    items: List[InternshipDashboardItem],
) -> UserDashboardStats:
    """Compute role-scoped statistics."""
    stats = UserDashboardStats()

    if not items:
        return stats

    stats.total_internships = len(items)
    stats.pending_approval = sum(1 for i in items if i.internship.status == "In Beoordeling")
    stats.approved = sum(1 for i in items if i.internship.status == "Goedgekeurd")
    stats.rejected = sum(1 for i in items if i.internship.status == "Afgekeurd")
    stats.ongoing = sum(1 for i in items if i.internship.status == "Lopend")
    stats.completed = sum(1 for i in items if i.internship.status == "Afgerond")
    stats.agreements_received = sum(1 for i in items if i.agreement_uploaded)
    stats.agreements_pending = sum(1 for i in items if i.internship.status in ("Goedgekeurd", "Overeenkomst Ingediend") and not i.agreement_uploaded)
    stats.agreements_validated = sum(1 for i in items if i.agreement_status == "Gevalideerd")

    return stats


def get_me_dashboard(db: Session, current_user: User) -> MeDashboardResponse:
    """Build the complete dashboard payload for the current user."""

    # 1. Fetch internships visible to this user (with eager loads)
    query = db.query(Internship).options(
        joinedload(Internship.student),
        joinedload(Internship.company),
        joinedload(Internship.teacher),
        joinedload(Internship.mentor),
        joinedload(Internship.proposal),
        joinedload(Internship.agreement),
    )

    if current_user.role == "student":
        query = query.filter(Internship.student_id == current_user.id)
    elif current_user.role == "teacher":
        query = query.filter(Internship.teacher_id == current_user.id)
    elif current_user.role == "mentor":
        query = query.filter(Internship.mentor_id == current_user.id)
    # Committee and admin see all

    internships = query.order_by(Internship.created_at.desc()).all()

    # 2. Fetch related data in bulk (avoid N+1)
    internship_ids = [i.id for i in internships]

    all_logbooks = (
        db.query(Logbook)
        .filter(Logbook.internship_id.in_(internship_ids))
        .all()
    ) if internship_ids else []

    all_evaluations = (
        db.query(Evaluation)
        .filter(Evaluation.internship_id.in_(internship_ids))
        .all()
    ) if internship_ids else []

    all_feedback = (
        db.query(Feedback)
        .filter(Feedback.internship_id.in_(internship_ids))
        .options(joinedload(Feedback.from_user))
        .all()
    ) if internship_ids else []

    # 3. Group by internship
    logbook_map = {iid: [] for iid in internship_ids}
    eval_map = {iid: [] for iid in internship_ids}
    feedback_map = {iid: [] for iid in internship_ids}

    for lb in all_logbooks:
        logbook_map.setdefault(lb.internship_id, []).append(lb)
    for ev in all_evaluations:
        eval_map.setdefault(ev.internship_id, []).append(ev)
    for fb in all_feedback:
        feedback_map.setdefault(fb.internship_id, []).append(fb)

    # 4. Build dashboard items
    items = []
    for internship in internships:
        item = _build_internship_dashboard_item(
            internship=internship,
            logbooks=logbook_map.get(internship.id, []),
            evaluations=eval_map.get(internship.id, []),
            feedbacks=feedback_map.get(internship.id, []),
        )
        items.append(item)

    # 5. Build alerts and stats
    alerts = _build_alerts(current_user, items)
    stats = _build_stats(current_user, items)

    return MeDashboardResponse(
        user=UserResponse.model_validate(current_user),
        role=current_user.role,
        internships=items,
        stats=stats,
        alerts=alerts,
        generated_at=datetime.now(UTC),
    )