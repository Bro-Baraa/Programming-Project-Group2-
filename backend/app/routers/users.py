"""User listing and lookup endpoints.

These endpoints allow the frontend to populate dropdowns
(teacher selection, mentor assignment, feedback recipients)
and to resolve user IDs to names across the app.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List users with optional role filter.

    Query params:
    - role: filter by role (student, teacher, committee, mentor, admin)
    - active_only: exclude deactivated users (default true)
    """
    if role and role not in {"student", "teacher", "committee", "mentor", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role}. Must be one of: student, teacher, committee, mentor, admin",
        )

    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if active_only:
        query = query.filter(User.is_active == True)

    users = query.order_by(User.last_name, User.first_name).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user