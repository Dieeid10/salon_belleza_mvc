from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

class RegisterSaleRequest(BaseModel):
    appointment_id: int = Field(gt=0)
    gossip_details: str | None = Field(default=None, max_length=250)

    @field_validator("gossip_details", mode="before")
    @classmethod
    def clean_gossip_details(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip()
        return value

class SaleDetailResponse(BaseModel):
    service_id: int | None
    discount_id: int | None
    list_price: Decimal | None
    service_discount_percentage: Decimal
    charged_price: Decimal

class SaleResponse(BaseModel):
    id: int
    date_time: datetime
    client_id: int | None
    employee_id: UUID | None
    appointment_id: int | None
    gossip_discount_id: int | None
    gossip_percentage: Decimal
    gossip_details: str | None
    subtotal: Decimal
    gossip_discount: Decimal
    total: Decimal
    details: list[SaleDetailResponse]