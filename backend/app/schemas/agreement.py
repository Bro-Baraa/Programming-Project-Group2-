"""Agreement schemas."""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class AgreementBase(BaseModel):
    insurance_verified: bool = False
    status: str = "Niet Ingediend"


class AgreementUpdate(BaseModel):
    insurance_verified: Optional[bool] = None
    status: Optional[str] = None


class AgreementResponse(AgreementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    internship_id: int
    file_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
