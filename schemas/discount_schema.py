from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class DiscountType(StrEnum):
    SERVICE = "service"
    GOSSIP = "gossip"


class DiscountRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: DiscountType
    percentage: Decimal = Field(gt=0, le=100, max_digits=5, decimal_places=2)
    service_id: int | None = Field(default=None, gt=0)
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_discount(self):
        if self.type is DiscountType.SERVICE and self.service_id is None:
            raise ValueError("El descuento de servicio requiere un servicio")
        if self.type is DiscountType.GOSSIP and self.service_id is not None:
            raise ValueError("El descuento chisme no se asocia a un servicio")
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("La fecha final no puede ser anterior a la inicial")
        return self


class DiscountResponse(BaseModel):
    id: int
    name: str
    type: DiscountType
    percentage: Decimal
    service_id: int | None
    start_date: date | None
    end_date: date | None
    is_active: bool