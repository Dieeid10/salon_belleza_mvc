from collections.abc import Iterator

from fastapi import APIRouter, Depends, Query, status
from psycopg import Connection

from app_mvc.controllers.professional_controller import ProfessionalController
from app_mvc.db.database import db
from app_mvc.models.professional_model import ProfessionalModel
from app_mvc.responses import success_response
from app_mvc.schemas.professional_schema import (
    ProfessionalRequest,
    ProfessionalResponse,
)
from app_mvc.security import require_role

router = APIRouter()
owner_only = [Depends(require_role("dueno"))]


def get_professional_controller() -> Iterator[ProfessionalController]:
    with db.transaction() as connection:
        yield ProfessionalController(ProfessionalModel(connection))


def serialize_professional(row: dict) -> dict:
    return ProfessionalResponse(
        id=row["id"],
        name=row["nombre"],
        profile_id=(str(row["perfil_id"]) if row["perfil_id"] is not None else None),
        is_active=row["activo"],
    ).model_dump(mode="json")


@router.get("/")
def list_professionals(
    only_active: bool = Query(default=True),
    controller: ProfessionalController = Depends(get_professional_controller),
):
    rows = controller.list_professionals(only_active)
    return success_response(
        [serialize_professional(row) for row in rows],
        "Profesionales obtenidos correctamente",
    )


@router.get("/{professional_id}")
def get_professional(
    professional_id: int,
    controller: ProfessionalController = Depends(get_professional_controller),
):
    row = controller.get_professional(professional_id)
    return success_response(
        serialize_professional(row),
        "Profesional obtenido correctamente",
    )


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=owner_only)
def create_professional(
    body: ProfessionalRequest,
    controller: ProfessionalController = Depends(get_professional_controller),
):
    row = controller.create_professional(body.model_dump())
    return success_response(
        serialize_professional(row),
        "Profesional creado correctamente",
        status.HTTP_201_CREATED,
    )


@router.put("/{professional_id}", dependencies=owner_only)
def update_professional(
    professional_id: int,
    body: ProfessionalRequest,
    controller: ProfessionalController = Depends(get_professional_controller),
):
    row = controller.update_professional(professional_id, body.model_dump())
    return success_response(
        serialize_professional(row),
        "Profesional actualizado correctamente",
    )


@router.delete("/{professional_id}", dependencies=owner_only)
def deactivate_professional(
    professional_id: int,
    controller: ProfessionalController = Depends(get_professional_controller),
):
    row = controller.deactivate_professional(professional_id)
    return success_response(
        serialize_professional(row),
        "Profesional desactivado correctamente",
    )