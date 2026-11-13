from app_mvc.errors import AppError


class AppointmentNotFound(AppError):
    status_code = 404
    code = "appointment_not_found"

    def __init__(self, appointment_id: int) -> None:
        super().__init__(f"Turno con ID {appointment_id} no encontrado")


class AppointmentNotCompleted(AppError):
    status_code = 422
    code = "appointment_not_completed"

    def __init__(self) -> None:
        super().__init__("Solo se puede cobrar un turno realizado")


class AppointmentHasNoDetails(AppError):
    status_code = 422
    code = "appointment_has_no_details"

    def __init__(self) -> None:
        super().__init__("El turno no tiene detalles cobrables")


class AppointmentAlreadySold(AppError):
    status_code = 409
    code = "appointment_already_sold"

    def __init__(self) -> None:
        super().__init__("Ya existe una venta para ese turno")


class GossipDiscountUnavailable(AppError):
    status_code = 422
    code = "gossip_discount_unavailable"

    def __init__(self) -> None:
        super().__init__("El descuento chisme no está disponible")


class SaleNotFound(AppError):
    status_code = 404
    code = "sale_not_found"

    def __init__(self, sale_id: int) -> None:
        super().__init__(f"Venta con ID {sale_id} no encontrada")