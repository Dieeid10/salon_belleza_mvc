from datetime import datetime
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator
)

class ClientRequest(BaseModel):
    """Cuerpo HTTP aceptado al crear o actualizar un cliente."""

    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    phone: str | None = Field(default=None, min_length=7, max_length=15)
    email: EmailStr | None = Field(default=None, max_length=254)

    @field_validator("first_name", "last_name", mode="before")
    def clean_name(cls, value: str) -> str:
        """Elimina espacios al inicio y final del nombre y apellido."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="before")
    def validate_contacte(self):
        if not self.phone and not self.email:
            raise ValueError("Se requiere al menos un teléfono o un correo electrónico")
        return self

class ClientResponse(BaseModel):
    """Forma pública de un cliente devuelta por la API."""

    id: int
    first_name: str
    last_name: str
    phone: str | None
    email: EmailStr | None
    is_active: bool
    created_at: datetime
    updated_at: datetime