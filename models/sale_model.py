from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from psycopg import Connection

from app_mvc.db.crud import Crud
from app_mvc.exceptions.sales import (
    SaleNotFound,
)

class SaleModel:
    """Lee y persiste ventas; la coordinación del cobro está en el controller."""

    TABLE = "ventas"
    DETAIL_TABLE = "detalle_ventas"

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self.crud = Crud(connection)

    def list_all(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT * FROM ventas ORDER BY fecha_hora DESC, id DESC"
        ).fetchall()
        details_by_sale = self._load_details([row["id"] for row in rows])
        return [
            self._to_response(row, details_by_sale.get(row["id"], []))
            for row in rows
        ]

    def get(self, sale_id: int) -> dict:
        row = self.crud.select(self.TABLE, sale_id)
        if row is None:
            raise SaleNotFound(sale_id)
        details = self._load_details([sale_id]).get(sale_id, [])
        return self._to_response(row, details)

    def exists_for_appointment(self, appointment_id: int) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM ventas WHERE turno_id = %s LIMIT 1",
            (appointment_id,),
        ).fetchone()
        return row is not None

    def create(
        self,
        appointment_id: int,
        client_id: int,
        employee_id: UUID,
        gossip_discount_id: int | None,
        gossip_percentage: Decimal,
        gossip_details: str | None,
        appointment_details: list[dict],
    ) -> dict:
        sale = self.crud.insert(
            self.TABLE,
            {
                "cliente_id": client_id,
                "empleado_id": employee_id,
                "turno_id": appointment_id,
                "descuento_chisme_id": gossip_discount_id,
                "chisme_pct": gossip_percentage,
                "chisme_detalle": gossip_details,
            },
        )

        for detail in appointment_details:
            self.crud.insert(
                self.DETAIL_TABLE,
                {
                    "venta_id": sale["id"],
                    "servicio_id": detail["service_id"],
                    "descuento_id": detail["discount_id"],
                    "precio_lista": detail["list_price"],
                    "descuento_pct": detail["service_discount_percentage"],
                    "precio_cobrado": detail["reserved_price"],
                },
            )

        return self.get(sale["id"])

    def _load_details(self, sale_ids: list[int]) -> dict[int, list[dict]]:
        """Carga los detalles en una consulta y los agrupa por venta."""
        if not sale_ids:
            return {}

        rows = self.connection.execute(
            """
            SELECT venta_id, servicio_id, descuento_id, precio_lista,
                   descuento_pct, precio_cobrado
            FROM detalle_ventas
            WHERE venta_id = ANY(%s)
            ORDER BY venta_id, id
            """,
            (sale_ids,),
        ).fetchall()

        details_by_sale: dict[int, list[dict]] = {}
        for row in rows:
            details_by_sale.setdefault(row["venta_id"], []).append(
                {
                    "service_id": row["servicio_id"],
                    "discount_id": row["descuento_id"],
                    "list_price": self._decimal_or_none(row["precio_lista"]),
                    "service_discount_percentage": Decimal(
                        str(row["descuento_pct"])
                    ),
                    "charged_price": Decimal(str(row["precio_cobrado"])),
                }
            )
        return details_by_sale

    @classmethod
    def _to_response(cls, row: dict, details: list[dict]) -> dict:
        subtotal = sum(
            (detail["charged_price"] for detail in details),
            Decimal("0.00"),
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gossip_percentage = Decimal(str(row["chisme_pct"]))
        gossip_discount_amount = (
            subtotal * gossip_percentage / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal - gossip_discount_amount).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        return {
            "id": row["id"],
            "date_time": row["fecha_hora"],
            "client_id": row["cliente_id"],
            "employee_id": row["empleado_id"],
            "appointment_id": row["turno_id"],
            "gossip_discount_id": row["descuento_chisme_id"],
            "gossip_percentage": gossip_percentage,
            "gossip_details": row["chisme_detalle"],
            "subtotal": subtotal,
            "gossip_discount": gossip_discount_amount,
            "total": total,
            "details": details,
        }

    @staticmethod
    def _decimal_or_none(value) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None