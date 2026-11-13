from collections.abc import Iterator

from fastapi import APIRouter, Depends, Query, status
from psycopg import Connection

from app_mvc.controllers.service_controller import ServiceController
from app_mvc.db.database import db
from app_mvc.models.service_model import ServiceModel
from app_mvc.responses import success_response
from app_mvc.schemas.service_schema import ServiceRequest, ServiceResponse
from app_mvc.security import require_role

router = APIRouter()
staff_access = [Depends(require_role("dueno", "vendedor"))]


def get_service_controller() -> Iterator[ServiceController]:
    with db.transaction() as connection:
        yield ServiceController(ServiceModel(connection))


def serialize_service(row: dict) -> dict:
    return ServiceResponse(
        id=row["id"],
        name=row["nombre_servicio"],
        description=row["descripcion"],
        price=row["precio"],
        duration_minutes=row["duracion_minutos"],
        visible_online=row["visible_online"],
        is_active=row["activo"],
    ).model_dump(mode="json")


@router.get("/")
def list_public_services(
    controller: ServiceController = Depends(get_service_controller),
):
    rows = controller.list_services()
    return success_response(
        [serialize_service(row) for row in rows],
        "Servicios obtenidos correctamente",
    )


@router.get("/management", dependencies=staff_access)
def list_managed_services(
    only_active: bool = Query(default=False),
    only_online: bool = Query(default=False),
    controller: ServiceController = Depends(get_service_controller),
):
    rows = controller.list_services(only_active, only_online)
    return success_response(
        [serialize_service(row) for row in rows],
        "Servicios de gestión obtenidos correctamente",
    )


@router.get("/management/{service_id}", dependencies=staff_access)
def get_managed_service(
    service_id: int,
    controller: ServiceController = Depends(get_service_controller),
):
    return success_response(
        serialize_service(controller.get_service(service_id)),
        "Servicio obtenido correctamente",
    )


@router.get("/{service_id}")
def get_public_service(
    service_id: int,
    controller: ServiceController = Depends(get_service_controller),
):
    return success_response(
        serialize_service(controller.get_public_service(service_id)),
        "Servicio obtenido correctamente",
    )


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=staff_access)
def create_service(
    body: ServiceRequest,
    controller: ServiceController = Depends(get_service_controller),
):
    row = controller.create_service(body.model_dump())
    return success_response(
        serialize_service(row),
        "Servicio creado correctamente",
        status.HTTP_201_CREATED,
    )


@router.put("/{service_id}", dependencies=staff_access)
def update_service(
    service_id: int,
    body: ServiceRequest,
    controller: ServiceController = Depends(get_service_controller),
):
    row = controller.update_service(service_id, body.model_dump())
    return success_response(
        serialize_service(row),
        "Servicio actualizado correctamente",
    )


@router.delete("/{service_id}", dependencies=staff_access)
def deactivate_service(
    service_id: int,
    controller: ServiceController = Depends(get_service_controller),
):
    row = controller.deactivate_service(service_id)
    return success_response(
        serialize_service(row),
        "Servicio desactivado correctamente",
    )