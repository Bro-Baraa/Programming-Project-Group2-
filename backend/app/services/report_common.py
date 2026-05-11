"""Shared report query helpers."""

from app.models import Internship


def apply_role_filter(query, user):
    """Apply role-based filtering to internship query."""
    if user.role == "student":
        return query.filter(Internship.student_id == user.id)
    if user.role == "mentor":
        return query.filter(Internship.mentor_id == user.id)
    if user.role == "teacher":
        return query.filter(Internship.teacher_id == user.id)
    return query
