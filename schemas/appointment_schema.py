from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, Field, field_validator


class AppointmentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ABSENT = "absent"


class BookAppointmentRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(pattern=r"^\+?\d{8,15}$")
    professional_id: int = Field(gt=0)
    service_ids: list[int] = Field(min_length=1)
    starts_at: AwareDatetime

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("service_ids")
    @classmethod
    def validate_service_ids(cls, values: list[int]) -> list[int]:
        if any(service_id <= 0 for service_id in values):
            raise ValueError("Los identificadores de servicio deben ser positivos")
        return values


class ChangeAppointmentStatusRequest(BaseModel):
    new_status: AppointmentStatus


class AppointmentDetailResponse(BaseModel):
    service_id: int
    name: str
    duration_minutes: int
    price: Decimal


class PublicAppointmentResponse(BaseModel):
    id: int
    professional_id: int
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    total: Decimal
    details: list[AppointmentDetailResponse]


class AppointmentResponse(PublicAppointmentResponse):
    client_id: int


class AvailabilityResponse(BaseModel):
    professional_id: int
    date: date
    duration_minutes: int
    available_starts: list[datetime]

class AppointmentSelection(BaseModel):
    professional_id: int = Field(gt=0)
    service_ids: list[int] = Field(min_length=1)
    starts_at: AwareDatetime

    @field_validator("service_ids")
    @classmethod
    def validate_service_ids(cls, values: list[int]) -> list[int]:
        if any(service_id <= 0 for service_id in values):
            raise ValueError("Los identificadores de servicio deben ser positivos")
        return values


class BookAppointmentRequest(AppointmentSelection):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(pattern=r"^\+?\d{8,15}$")

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class BookAccountAppointmentRequest(AppointmentSelection):
    phone: str | None = Field(default=None, pattern=r"^\+?\d{8,15}$")