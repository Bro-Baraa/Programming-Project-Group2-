import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import timedelta
from pathlib import Path
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.auth import (
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    get_current_active_user,
    require_admin,
)
from app.services.audit import log_event

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

# Cookies are sent only over HTTPS by default. Set COOKIE_SECURE=false to test
# the cookie flow over plain http (e.g. local dev / e2e on localhost).
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"


def _load_seed_emails() -> set:
    """Load seed user emails from seed_data.yaml for demo-login validation."""
    seed_path = Path(__file__).resolve().parents[2] / "seed_data.yaml"
    try:
        import yaml

        with open(seed_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        users = data.get("users", [])
        return {u["email"] for u in users if "email" in u}
    except Exception:
        return set()


@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        logger.warning("[LOGIN FAILED] Unknown email: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(
            "[LOGIN FAILED] Inactive user attempted login: %s (id=%s)",
            user.email,
            user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.password_hash):
        logger.warning(
            "[LOGIN FAILED] Wrong password for user: %s (id=%s)", user.email, user.id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("[LOGIN SUCCESS] %s (id=%s, role=%s)", user.email, user.id, user.role)
    log_event(
        db,
        "login",
        user=user,
        entity_type="user",
        entity_id=user.id,
        detail="Succesvol ingelogd",
    )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=int(access_token_expires.total_seconds()),
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    db_user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


class DemoLoginRequest(BaseModel):
    email: str


@router.post("/demo-login", response_model=Token)
def demo_login(
    response: Response, request: DemoLoginRequest, db: Session = Depends(get_db)
):
    """
    One-click login for demo accounts. No password required.
    Restricted to pre-seeded demo users.
    """
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.warning("[DEMO LOGIN FAILED] Unknown email: %s", request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        logger.warning(
            "[DEMO LOGIN FAILED] Inactive user: %s (id=%s)", user.email, user.id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive",
        )

    # Only allow demo-login for pre-seeded accounts
    # This prevents bypassing real user passwords.
    seed_emails = _load_seed_emails()
    if user.email not in seed_emails:
        logger.warning("[DEMO LOGIN FAILED] Not a seed account: %s", user.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login only available for test accounts",
        )

    logger.info(
        "[DEMO LOGIN SUCCESS] %s (id=%s, role=%s)", user.email, user.id, user.role
    )
    log_event(
        db,
        "login",
        user=user,
        entity_type="user",
        entity_id=user.id,
        detail="Demo login",
    )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=int(access_token_expires.total_seconds()),
        path="/",
    )

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/logout")
def logout(response: Response):
    """Clear the httpOnly cookie on logout."""
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return {"message": "Uitgelogd"}
