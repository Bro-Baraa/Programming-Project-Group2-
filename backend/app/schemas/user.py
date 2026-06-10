from pydantic import BaseModel, EmailStr, ConfigDict, Field

from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr = Field(
        ..., description="Uniek e-mailadres van de gebruiker (gebruikt om in te loggen)"
    )
    first_name: str = Field(..., description="Voornaam van de gebruiker")
    last_name: str = Field(..., description="Achternaam van de gebruiker")
    role: str = Field(
        ...,
        description="Rol van de gebruiker (bijv. student, teacher, mentor, committee, of admin)",
    )


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
    first_name: str
    last_name: str
    role: str
