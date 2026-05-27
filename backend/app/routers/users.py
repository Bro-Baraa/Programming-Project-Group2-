"""User listing and lookup endpoints.

These endpoints allow the frontend to populate dropdowns
(teacher selection, mentor assignment, feedback recipients)
and to resolve user IDs to names across the app.
"""

from typing import List, Optional, Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.auth import get_current_active_user
from app.dependencies import pagination

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
def list_users(
    response: Response,
    role: Optional[str] = None,
    active_only: bool = True,
    search: Annotated[Optional[str], Query(min_length=1, max_length=100, description="Search first name, last name, or email")] = None,
    pag: Annotated[dict, Depends(pagination)] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List users with optional role filter, search, and pagination.

    Query params:
    - role: filter by role (student, teacher, committee, mentor, admin)
    - active_only: exclude deactivated users (default true)
    - search: keyword search across first_name, last_name, email
    - skip / limit: pagination (default limit=50, max=200)

    Response headers:
    - X-Total-Count: total matching items
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

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term),
            )
        )

    # Count total
    total_count = query.with_entities(func.count(User.id)).scalar()
    response.headers["X-Total-Count"] = str(total_count)

    # Pagination
    skip = pag.get("skip", 0) if pag else 0
    limit = pag.get("limit", 50) if pag else 50
    users = query.order_by(User.last_name, User.first_name).offset(skip).limit(limit).all()
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