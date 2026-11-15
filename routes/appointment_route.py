from datetime import date
from zoneinfo import ZoneInfo
from uuid import UUID

from fastapi import HTTPException

from fastapi import APIRouter, Depends, Query, status
from psycopg import Connection

from app_mvc.config.config import settings
from app_mvc.controllers.appointment_controller import AppointmentController
from app_mvc.db.database import get_db_connection
from app_mvc.models.appointment_model import AppointmentModel
from app_mvc.models.client_model import ClientModel
from app_mvc.models.professional_model import ProfessionalModel
from app_mvc.models.service_model import ServiceModel
from app_mvc.responses import success_response
from app_mvc.schemas.appointment_schema import (
    AppointmentResponse,
    AppointmentStatus,
    AvailabilityResponse,
    BookAppointmentRequest,
    ChangeAppointmentStatusRequest,
    PublicAppointmentResponse,
    BookAccountAppointmentRequest,
)
from app_mvc.security import require_role, current_user

public_router = APIRouter()
admin_router = APIRouter(
    dependencies=[Depends(require_role("dueno", "vendedor"))],
)
def get_appointment_controller(
    connection: Connection = Depends(get_db_connection),
) -> AppointmentController:
    salon_timezone = ZoneInfo(settings.zona_horaria)
    return AppointmentController(
        appointments=AppointmentModel(
            connection,
            salon_timezone,
        ),
        clients=ClientModel(connection),
        professionals=ProfessionalModel(connection),
        services=ServiceModel(connection),
        salon_timezone=salon_timezone,
    )


def serialize_public_appointment(appointment: dict) -> dict:
    public_data = {key: value for key, value in appointment.items() if key != "client_id"}
    return PublicAppointmentResponse.model_validate(public_data).model_dump(mode="json")


def serialize_appointment(appointment: dict) -> dict:
    return AppointmentResponse.model_validate(appointment).model_dump(mode="json")


@public_router.get("/availability")
def check_availability(
    day: date,
    professional_id: int = Query(gt=0),
    service_ids: list[int] = Query(min_length=1),
    controller: AppointmentController = Depends(get_appointment_controller),
):
    result = controller.check_availability(professional_id, day, service_ids)
    return success_response(
        AvailabilityResponse.model_validate(result).model_dump(mode="json"),
        "Disponibilidad obtenida correctamente",
    )


@public_router.post("/", status_code=status.HTTP_201_CREATED)
def book_public_appointment(
    body: BookAppointmentRequest,
    controller: AppointmentController = Depends(get_appointment_controller),
):
    appointment = controller.book(body.model_dump(), guest_only=True)
    return success_response(
        serialize_public_appointment(appointment),
        "Turno reservado correctamente",
        status.HTTP_201_CREATED,
    )

@public_router.post("/me", status_code=status.HTTP_201_CREATED)
def book_account_appointment(
    body: BookAccountAppointmentRequest,
    user: dict = Depends(current_user),
    controller: AppointmentController = Depends(get_appointment_controller),
):
    subject = user.get("sub")

    try:
        user_id = UUID(subject) if isinstance(subject, str) else None
    except ValueError:
        user_id = None

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identidad de sesión inválida",
        )

    appointment = controller.book(body.model_dump(), user_id=user_id)

    return success_response(
        serialize_public_appointment(appointment),
        "Turno reservado correctamente",
        status.HTTP_201_CREATED,
    )

@admin_router.get("/")
def list_appointments(
    start_date: date,
    end_date: date,
    professional_id: int | None = Query(default=None, gt=0),
    appointment_status: AppointmentStatus | None = Query(default=None, alias="status"),
    controller: AppointmentController = Depends(get_appointment_controller),
):
    appointments = controller.list_appointments(
        start_date,
        end_date,
        professional_id,
        appointment_status,
    )
    return success_response(
        [serialize_appointment(appointment) for appointment in appointments],
        "Turnos obtenidos correctamente",
    )


@admin_router.get("/{appointment_id}")
def get_appointment(
    appointment_id: int,
    controller: AppointmentController = Depends(get_appointment_controller),
):
    return success_response(
        serialize_appointment(controller.get_appointment(appointment_id)),
        "Turno obtenido correctamente",
    )


@admin_router.post("/", status_code=status.HTTP_201_CREATED)
def book_staff_appointment(
    body: BookAppointmentRequest,
    controller: AppointmentController = Depends(get_appointment_controller),
):
    appointment = controller.book(body.model_dump())
    return success_response(
        serialize_appointment(appointment),
        "Turno reservado correctamente",
        status.HTTP_201_CREATED,
    )


@admin_router.post("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    controller: AppointmentController = Depends(get_appointment_controller),
):
    return success_response(
        serialize_appointment(controller.cancel(appointment_id)),
        "Turno cancelado correctamente",
    )


@admin_router.patch("/{appointment_id}/status")
def change_appointment_status(
    appointment_id: int,
    body: ChangeAppointmentStatusRequest,
    controller: AppointmentController = Depends(get_appointment_controller),
):
    return success_response(
        serialize_appointment(
            controller.change_status(appointment_id, body.new_status)
        ),
        "Estado del turno actualizado correctamente",
    )