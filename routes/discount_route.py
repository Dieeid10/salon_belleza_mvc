from collections.abc import Iterator
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, status
from psycopg import Connection

from app_mvc.config.config import settings
from app_mvc.controllers.discount_controller import DiscountController
from app_mvc.db.database import db
from app_mvc.models.discount_model import DiscountModel
from app_mvc.responses import success_response
from app_mvc.schemas.discount_schema import DiscountRequest, DiscountResponse
from app_mvc.security import require_role

router = APIRouter()
owner_only = [Depends(require_role("dueno"))]
BUSINESS_TIMEZONE = ZoneInfo(settings.zona_horaria)


def get_discount_controller() -> Iterator[DiscountController]:
    with db.transaction() as connection:
        yield DiscountController(DiscountModel(connection))


def serialize_discount(row: dict) -> dict:
    return DiscountResponse.model_validate(row).model_dump(mode="json")


@router.get("/")
def list_public_discounts(
    controller: DiscountController = Depends(get_discount_controller),
):
    today = datetime.now(BUSINESS_TIMEZONE).date()
    rows = controller.list_public_discounts(today)
    return success_response(
        [serialize_discount(row) for row in rows],
        "Descuentos públicos obtenidos correctamente",
    )


@router.get("/management", dependencies=owner_only)
def list_discounts(
    controller: DiscountController = Depends(get_discount_controller),
):
    rows = controller.list_discounts()
    return success_response(
        [serialize_discount(row) for row in rows],
        "Descuentos obtenidos correctamente",
    )


@router.get("/management/{discount_id}", dependencies=owner_only)
def get_discount(
    discount_id: int,
    controller: DiscountController = Depends(get_discount_controller),
):
    return success_response(
        serialize_discount(controller.get_discount(discount_id)),
        "Descuento obtenido correctamente",
    )


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=owner_only)
def create_discount(
    body: DiscountRequest,
    controller: DiscountController = Depends(get_discount_controller),
):
    row = controller.create_discount(body.model_dump())
    return success_response(
        serialize_discount(row),
        "Descuento creado correctamente",
        status.HTTP_201_CREATED,
    )


@router.put("/{discount_id}", dependencies=owner_only)
def update_discount(
    discount_id: int,
    body: DiscountRequest,
    controller: DiscountController = Depends(get_discount_controller),
):
    row = controller.update_discount(discount_id, body.model_dump())
    return success_response(
        serialize_discount(row),
        "Descuento actualizado correctamente",
    )


@router.delete("/{discount_id}", dependencies=owner_only)
def deactivate_discount(
    discount_id: int,
    controller: DiscountController = Depends(get_discount_controller),
):
    row = controller.deactivate_discount(discount_id)
    return success_response(
        serialize_discount(row),
        "Descuento desactivado correctamente",
    )