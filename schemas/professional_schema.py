from pydantic import BaseModel, Field, field_validator


class ProfessionalRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    profile_id: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class ProfessionalResponse(BaseModel):
    id: int
    name: str
    profile_id: str | None
    is_active: bool