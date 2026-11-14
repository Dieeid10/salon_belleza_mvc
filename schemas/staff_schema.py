from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class InviteSellerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=254)

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class StaffResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr | None
    role: str
    created_at: datetime


class StaffInvitationResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str