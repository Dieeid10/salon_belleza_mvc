from collections.abc import Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app_mvc.controllers.sale_controller import SaleController
from app_mvc.db.database import db
from app_mvc.models.appointment_model import AppointmentModel
from app_mvc.models.discount_model import DiscountModel
from app_mvc.models.sale_model import SaleModel
from app_mvc.responses import success_response
from app_mvc.schemas.sale_schema import RegisterSaleRequest, SaleResponse
from app_mvc.security import require_role

router = APIRouter()
sales_access = require_role("dueno", "vendedor")


def get_sale_controller() -> Iterator[SaleController]:
	"""Crea los tres modelos con la conexión transaccional de esta petición."""
	with db.transaction() as connection:
		yield SaleController(
			sales=SaleModel(connection),
			appointments=AppointmentModel(connection),
			discounts=DiscountModel(connection),
		)


def serialize_sale(sale: dict) -> dict:
	return SaleResponse.model_validate(sale).model_dump(mode="json")


@router.get("/", dependencies=[Depends(sales_access)])
def list_sales(
	controller: SaleController = Depends(get_sale_controller),
):
	return success_response(
		[serialize_sale(sale) for sale in controller.list_sales()],
		"Ventas obtenidas correctamente",
	)


@router.get("/{sale_id}", dependencies=[Depends(sales_access)])
def get_sale(
	sale_id: int,
	controller: SaleController = Depends(get_sale_controller),
):
	return success_response(
		serialize_sale(controller.get_sale(sale_id)),
		"Venta obtenida correctamente",
	)


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_sale(
	body: RegisterSaleRequest,
	staff: dict = Depends(sales_access),
	controller: SaleController = Depends(get_sale_controller),
):
	try:
		employee_id = UUID(staff["sub"])
	except (KeyError, ValueError) as error:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="La identidad del empleado no es válida",
		) from error

	sale = controller.register_sale(
		appointment_id=body.appointment_id,
		employee_id=employee_id,
		gossip_details=body.gossip_details,
	)
	return success_response(
		serialize_sale(sale),
		"Venta registrada correctamente",
		status.HTTP_201_CREATED,
	)
