"""User listing and lookup endpoints.

These endpoints allow the frontend to populate dropdowns
(teacher selection, mentor assignment, feedback recipients)
and to resolve user IDs to names across the app.
"""

from typing import List, Optional, Annotated
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.database import get_db
from app.models import User, Internship
from app.schemas import UserResponse, UserCreate, UserUpdate, SeedUser
from app.auth import get_current_active_user, get_password_hash
from app.dependencies import pagination
from app.services.audit import log_event

router = APIRouter(prefix="/users", tags=["users"])


def _load_seed_users() -> list[dict]:
    """Load test accounts from seed_data.yaml for the login page dropdown."""
    seed_path = Path(__file__).resolve().parents[2] / "seed_data.yaml"
    try:
        import yaml

        with open(seed_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        users = data.get("users", [])
        return [
            {
                "email": u["email"],
                "first_name": u["first_name"],
                "last_name": u["last_name"],
                "role": u["role"],
            }
            for u in users
            if "email" in u
        ]
    except Exception:
        return []


@router.get("/seed", response_model=list[SeedUser])
def get_seed_users():
    """Return test accounts from seed_data.yaml for the quick-login dropdown."""
    return _load_seed_users()


@router.get("", response_model=List[UserResponse])
def list_users(
    response: Response,
    role: Optional[str] = None,
    active_only: bool = True,
    search: Annotated[
        Optional[str],
        Query(
            min_length=1,
            max_length=100,
            description="Search first name, last name, or email",
        ),
    ] = None,
    pag: Annotated[dict, Depends(pagination)] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
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
    users = (
        query.order_by(User.last_name, User.first_name).offset(skip).limit(limit).all()
    )
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):

    # Check for duplicate email
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {data.email} already exists",
        )

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(
        db,
        "user.create",
        user=current_user,
        entity_type="user",
        entity_id=user.id,
        detail=f"Gebruiker aangemaakt: {user.email} ({user.role})",
    )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if data.email is not None:
        user.email = data.email
    if data.first_name is not None:
        user.first_name = data.first_name
    if data.last_name is not None:
        user.last_name = data.last_name
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)
    log_event(
        db,
        "user.update",
        user=current_user,
        entity_type="user",
        entity_id=user.id,
        detail=f"Gebruiker gewijzigd: {user.email}",
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Guard: prevent deletion if user has related internships
    related = (
        db.query(Internship)
        .filter(
            or_(
                Internship.student_id == user_id,
                Internship.teacher_id == user_id,
                Internship.mentor_id == user_id,
            )
        )
        .first()
    )
    if related:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete user: they have related internships",
        )

    db.delete(user)
    db.commit()
    log_event(
        db,
        "user.delete",
        user=current_user,
        entity_type="user",
        entity_id=user_id,
        detail=f"Gebruiker verwijderd: {user.email}",
    )
    return None
