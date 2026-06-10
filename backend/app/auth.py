import logging
import os
from datetime import datetime, timedelta, UTC
from typing import Optional
from dotenv import load_dotenv
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User

# Load .env if present (development convenience)
load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable must be set. "
        "Create backend/.env from .env.example or set it manually."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("[TOKEN FAILED] Token expired")
        return None
    except JWTError as e:
        logger.warning("[TOKEN FAILED] Invalid token: %s", e)
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("[TOKEN FAILED] Token missing 'sub' claim")
        raise credentials_exception

    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        logger.warning("[TOKEN FAILED] Invalid user_id in token: %s", user_id)
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id_int).first()
    if user is None:
        logger.warning("[TOKEN FAILED] User not found for id=%s", user_id_int)
        raise credentials_exception

    if not user.is_active:
        logger.warning(
            "[TOKEN FAILED] Inactive user attempted access: %s (id=%s)",
            user.email,
            user.id,
        )
        raise credentials_exception

    logger.debug("[AUTH OK] %s (id=%s, role=%s)", user.email, user.id, user.role)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(required_roles: list):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return current_user

    return role_checker


# Role shortcuts
require_student = require_role(["student"])
require_teacher = require_role(["teacher"])
require_committee = require_role(["committee"])
require_mentor = require_role(["mentor"])
require_admin = require_role(["admin"])
require_teacher_or_committee = require_role(["teacher", "committee"])
require_any_staff = require_role(["teacher", "committee", "mentor", "admin"])
require_committee_or_admin = require_role(["committee", "admin"])
