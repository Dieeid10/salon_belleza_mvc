from decimal import Decimal
from uuid import UUID

from app_mvc.exceptions.sales import (
    AppointmentAlreadySold,
    AppointmentHasNoDetails,
    AppointmentNotCompleted,
    AppointmentNotFound,
    GossipDiscountUnavailable,
)
from app_mvc.models.appointment_model import AppointmentModel
from app_mvc.models.discount_model import DiscountModel
from app_mvc.models.sale_model import SaleModel


class SaleController:
    """Coordina la regla de cobro entre ventas, turnos y descuentos."""

    def __init__(
        self,
        sales: SaleModel,
        appointments: AppointmentModel,
        discounts: DiscountModel,
    ) -> None:
        self.sales = sales
        self.appointments = appointments
        self.discounts = discounts

    def list_sales(self) -> list[dict]:
        return self.sales.list_all()

    def get_sale(self, sale_id: int) -> dict:
        return self.sales.get(sale_id)

    def register_sale(
        self,
        appointment_id: int,
        employee_id: UUID,
        gossip_details: str | None = None,
    ) -> dict:
        appointment = self.appointments.get_for_sale(appointment_id)
        if appointment is None:
            raise AppointmentNotFound(appointment_id)
        if appointment["status"] != "Realizado":
            raise AppointmentNotCompleted()

        appointment_details = self.appointments.get_details_for_sale(appointment_id)
        if not appointment_details:
            raise AppointmentHasNoDetails()
        if self.sales.exists_for_appointment(appointment_id):
            raise AppointmentAlreadySold()

        gossip_details = gossip_details.strip() if gossip_details else None
        gossip_discount = None
        if gossip_details:
            gossip_discount = self.discounts.get_active_gossip_discount()
            if gossip_discount is None:
                raise GossipDiscountUnavailable()

        gossip_percentage = (
            Decimal(str(gossip_discount["percentage"]))
            if gossip_discount is not None
            else Decimal("0")
        )

        return self.sales.create(
            appointment_id=appointment_id,
            client_id=appointment["client_id"],
            employee_id=employee_id,
            gossip_discount_id=(
                gossip_discount["id"] if gossip_discount is not None else None
            ),
            gossip_percentage=gossip_percentage,
            gossip_details=gossip_details,
            appointment_details=appointment_details,
        )