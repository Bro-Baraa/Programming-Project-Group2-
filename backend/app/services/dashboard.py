from collections import defaultdict
from datetime import datetime, UTC

from sqlalchemy.orm import Session, joinedload

from app.models import Feedback, Internship, Logbook, Evaluation, User
from app.schemas import (
    InternshipDashboardItem,
    UserDashboardStats,
    DashboardAlert,
    MeDashboardResponse,
    UserResponse,
    InternshipListResponse,
    FeedbackResponse,
)


def get_me_dashboard(db: Session, current_user: User) -> MeDashboardResponse:
    role = current_user.role

    query = db.query(Internship).options(
        joinedload(Internship.student),
        joinedload(Internship.company),
        joinedload(Internship.teacher),
        joinedload(Internship.mentor),
        joinedload(Internship.proposal),
        joinedload(Internship.agreement),
    )

    if role == "student":
        query = query.filter(Internship.student_id == current_user.id)
    elif role == "teacher":
        query = query.filter(Internship.teacher_id == current_user.id)
    elif role == "mentor":
        query = query.filter(Internship.mentor_id == current_user.id)

    internships = query.order_by(Internship.created_at.desc()).all()
    if not internships:
        return MeDashboardResponse(
            user=UserResponse.model_validate(current_user),
            role=role,
            stats=UserDashboardStats(),
            generated_at=datetime.now(UTC),
        )

    ids = [i.id for i in internships]

    logbook_map = defaultdict(list)
    eval_map = defaultdict(list)
    feedback_map = defaultdict(list)

    for lb in db.query(Logbook).filter(Logbook.internship_id.in_(ids)).all():
        logbook_map[lb.internship_id].append(lb)
    for ev in db.query(Evaluation).filter(Evaluation.internship_id.in_(ids)).all():
        eval_map[ev.internship_id].append(ev)
    for fb in (
        db.query(Feedback)
        .filter(Feedback.internship_id.in_(ids))
        .options(joinedload(Feedback.from_user))
        .all()
    ):
        feedback_map[fb.internship_id].append(fb)

    items = []
    for i in internships:
        logbooks = logbook_map[i.id]
        evaluations = eval_map[i.id]
        feedbacks = feedback_map[i.id]

        total_weeks = 0
        next_due_week = None
        if i.start_date and i.end_date:
            total_days = (i.end_date - i.start_date).days
            total_weeks = max(1, (total_days // 7) + 1)

        existing_weeks = {lb.week_number for lb in logbooks}
        submitted = sum(1 for lb in logbooks if lb.status == "submitted")
        draft = sum(1 for lb in logbooks if lb.status == "draft")
        missing = max(0, total_weeks - len(existing_weeks))

        if total_weeks > 0:
            for week in range(1, total_weeks + 1):
                if week not in existing_weeks:
                    next_due_week = week
                    break

        eval_count = len(evaluations)
        finalized = sum(1 for ev in evaluations if ev.finalized)
        latest = max(evaluations, key=lambda ev: ev.created_at) if evaluations else None
        recent = sorted(feedbacks, key=lambda f: f.created_at, reverse=True)[:3]

        items.append(
            InternshipDashboardItem(
                internship=InternshipListResponse.model_validate(i),
                proposal_status=i.proposal.status if i.proposal else None,
                agreement_status=i.agreement.status if i.agreement else None,
                agreement_uploaded=i.agreement is not None,
                total_weeks=total_weeks,
                logbooks_submitted=submitted,
                logbooks_missing=missing,
                logbooks_draft=draft,
                next_due_week=next_due_week,
                evaluations_count=eval_count,
                evaluations_finalized=finalized,
                latest_evaluation_status=latest.status if latest else None,
                recent_feedback=[FeedbackResponse.model_validate(f) for f in recent],
            )
        )

    alerts = []
    for item in items:
        i = item.internship
        student_name = f"{i.student.first_name} {i.student.last_name}"

        def _alert(severity, message, url=None, entity_type="internship"):
            alerts.append(
                DashboardAlert(
                    severity=severity,
                    message=message,
                    action_url=url,
                    entity_type=entity_type,
                    entity_id=i.id,
                )
            )

        if role == "student":
            if i.status == "Aanpassingen Vereist":
                _alert(
                    "warning",
                    "Je stagevoorstel heeft aanpassingen nodig. Bekijk de feedback en dien opnieuw in.",
                    "?view=voorstel",
                )
            if i.status == "Goedgekeurd" and not item.agreement_uploaded:
                _alert(
                    "warning",
                    "Je stage is goedgekeurd. Upload je ondertekende overeenkomst.",
                    "?view=overeenkomst",
                )
            if item.next_due_week and i.status == "Lopend":
                _alert(
                    "info",
                    f"Week {item.next_due_week} logboek nog niet ingevuld.",
                    "?view=logboek",
                    "logbook",
                )

        if role == "teacher":
            pending = item.logbooks_submitted - item.evaluations_count
            if item.logbooks_submitted > 0 and pending > 0:
                _alert(
                    "info",
                    f"{pending} logboek(en) in afwachting van evaluatie bij {student_name}.",
                )

        if role in ("committee", "admin"):
            if i.status == "In Beoordeling":
                _alert(
                    "warning",
                    f"Voorstel van {student_name} wacht op beoordeling.",
                    "?view=voorstellen",
                )
            if item.agreement_status == "Ingediend":
                _alert(
                    "info",
                    f"Overeenkomst van {student_name} wacht op validatie.",
                    "?view=overzicht",
                )

        if role == "mentor" and item.logbooks_submitted > 0:
            _alert(
                "info",
                f"Nieuwe logboeken ingediend door {student_name}.",
                "?view=validatie",
            )

    alerts.sort(key=lambda a: {"error": 0, "warning": 1, "info": 2}[a.severity])

    stats = UserDashboardStats()
    if items:

        def _count(pred):
            return sum(1 for item in items if pred(item))

        stats.total_internships = len(items)
        stats.pending_approval = _count(
            lambda x: x.internship.status == "In Beoordeling"
        )
        stats.approved = _count(lambda x: x.internship.status == "Goedgekeurd")
        stats.rejected = _count(lambda x: x.internship.status == "Afgekeurd")
        stats.ongoing = _count(lambda x: x.internship.status == "Lopend")
        stats.completed = _count(lambda x: x.internship.status == "Afgerond")
        stats.stopped = _count(lambda x: x.internship.status == "Stopgezet")
        stats.agreements_received = _count(lambda x: x.agreement_uploaded)
        stats.agreements_pending = _count(
            lambda x: x.internship.status in ("Goedgekeurd", "Overeenkomst Ingediend")
            and not x.agreement_uploaded
        )
        stats.agreements_validated = _count(
            lambda x: x.agreement_status == "Gevalideerd"
        )

    return MeDashboardResponse(
        user=UserResponse.model_validate(current_user),
        role=role,
        internships=items,
        stats=stats,
        alerts=alerts,
        generated_at=datetime.now(UTC),
    )
