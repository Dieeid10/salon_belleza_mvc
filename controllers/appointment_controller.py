from datetime import date, datetime, time, timedelta, timezone, tzinfo

from app_mvc.exceptions.appointments import (
    AppointmentInPast,
    AppointmentWithoutServices,
    InvalidDateRange,
    ProfessionalUnavailable,
    ServiceUnavailable,
    TimeSlotUnavailable,
)
from app_mvc.models.appointment_model import AppointmentModel
from app_mvc.models.client_model import ClientModel
from app_mvc.models.professional_model import ProfessionalModel
from app_mvc.models.service_model import ServiceModel
from app_mvc.schemas.appointment_schema import AppointmentStatus


class AppointmentController:
    """Coordina la reserva, disponibilidad y gestión de turnos."""

    def __init__(
        self,
        appointments: AppointmentModel,
        clients: ClientModel,
        professionals: ProfessionalModel,
        services: ServiceModel,
        salon_timezone: tzinfo,
    ) -> None:
        self.appointments = appointments
        self.clients = clients
        self.professionals = professionals
        self.services = services
        self.salon_timezone = salon_timezone

    def check_availability(
        self,
        professional_id: int,
        day: date,
        service_ids: list[int],
    ) -> dict:
        self._validate_professional(professional_id)
        services = self._get_active_services(service_ids)
        duration = timedelta(
            minutes=sum(service["duration_minutes"] for service in services)
        )
        schedule = self.appointments.schedule_for(professional_id, day)
        available_starts = []
        if schedule:
            busy = self.appointments.occupied_slots(
                professional_id,
                min(opening for opening, _ in schedule),
                max(closing for _, closing in schedule),
            )
            available_starts = self.appointments.available_starts(
                schedule,
                busy,
                duration,
                datetime.now(timezone.utc),
            )
        return {
            "professional_id": professional_id,
            "date": day,
            "duration_minutes": int(duration.total_seconds() // 60),
            "available_starts": available_starts,
        }

    def book(self, data: dict) -> dict:
        professional_id = data["professional_id"]
        self._validate_professional(professional_id)
        services = self._get_active_services(data["service_ids"])

        starts_at = data["starts_at"]
        now = datetime.now(timezone.utc)
        if starts_at <= now:
            raise AppointmentInPast()

        duration = timedelta(
            minutes=sum(service["duration_minutes"] for service in services)
        )
        ends_at = starts_at + duration
        local_day = starts_at.astimezone(self.salon_timezone).date()
        schedule = self.appointments.schedule_for(professional_id, local_day)
        busy = self.appointments.occupied_slots(professional_id, starts_at, ends_at)
        if not self.appointments.is_available(starts_at, ends_at, schedule, busy):
            raise TimeSlotUnavailable()

        client_id = self.clients.get_or_create_for_appointment(
            data["first_name"],
            data["last_name"],
            data["phone"],
        )
        return self.appointments.create(
            client_id=client_id,
            professional_id=professional_id,
            starts_at=starts_at,
            ends_at=ends_at,
            services=services,
        )

    def list_appointments(
        self,
        start_date: date,
        end_date: date,
        professional_id: int | None = None,
        status: AppointmentStatus | None = None,
    ) -> list[dict]:
        if end_date < start_date:
            raise InvalidDateRange()
        starts_at = datetime.combine(start_date, time.min, self.salon_timezone)
        ends_at = datetime.combine(
            end_date + timedelta(days=1),
            time.min,
            self.salon_timezone,
        )
        return self.appointments.list_all(
            starts_at,
            ends_at,
            professional_id,
            status,
        )

    def get_appointment(self, appointment_id: int) -> dict:
        return self.appointments.get(appointment_id)

    def cancel(self, appointment_id: int) -> dict:
        return self.appointments.cancel(appointment_id, datetime.now(timezone.utc))

    def change_status(
        self,
        appointment_id: int,
        new_status: AppointmentStatus,
    ) -> dict:
        return self.appointments.change_status(
            appointment_id,
            new_status,
            datetime.now(timezone.utc),
        )

    def _validate_professional(self, professional_id: int) -> None:
        if not self.professionals.is_active(professional_id):
            raise ProfessionalUnavailable()

    def _get_active_services(self, service_ids: list[int]) -> list[dict]:
        unique_ids = list(dict.fromkeys(service_ids))
        if not unique_ids:
            raise AppointmentWithoutServices()
        services = self.services.get_active_by_ids(unique_ids)
        if len(services) != len(unique_ids):
            raise ServiceUnavailable()
        return services