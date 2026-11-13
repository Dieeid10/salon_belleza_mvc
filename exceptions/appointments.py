from app_mvc.errors import AppError


class AppointmentNotFound(AppError):
    status_code = 404
    code = "appointment_not_found"

    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"Turno con ID {appointment_id} no encontrado")


class ProfessionalUnavailable(AppError):
    status_code = 404
    code = "professional_unavailable"

    def __init__(self) -> None:
        super().__init__("El profesional no existe o no está activo")


class ServiceUnavailable(AppError):
    status_code = 404
    code = "service_unavailable"

    def __init__(self) -> None:
        super().__init__("Uno o más servicios no existen o no están activos")


class AppointmentWithoutServices(AppError):
    status_code = 422
    code = "appointment_without_services"

    def __init__(self) -> None:
        super().__init__("El turno necesita al menos un servicio")


class AppointmentInPast(AppError):
    status_code = 422
    code = "appointment_in_past"

    def __init__(self) -> None:
        super().__init__("No se puede reservar un turno en el pasado")


class AppointmentNotStarted(AppError):
    status_code = 422
    code = "appointment_not_started"

    def __init__(self) -> None:
        super().__init__("El turno todavía no comenzó")


class InvalidStatusTransition(AppError):
    status_code = 409
    code = "invalid_appointment_status_transition"

    def __init__(self, current: str, requested: str) -> None:
        super().__init__(f"No se puede cambiar el estado de {current} a {requested}")


class TimeSlotUnavailable(AppError):
    status_code = 409
    code = "time_slot_unavailable"

    def __init__(self) -> None:
        super().__init__("El horario elegido ya no está disponible")


class InvalidDateRange(AppError):
    status_code = 422
    code = "invalid_date_range"

    def __init__(self) -> None:
        super().__init__("La fecha inicial debe ser anterior o igual a la fecha final")