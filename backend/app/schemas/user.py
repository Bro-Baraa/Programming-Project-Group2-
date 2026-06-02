"""User schemas."""
from pydantic import BaseModel, EmailStr, ConfigDict

from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SeedUser(BaseModel):
    """Test account from seed_data.yaml (used by login page dropdown)."""
    email: str
    password: str
    first_name: str
    last_name: str
    role: str
