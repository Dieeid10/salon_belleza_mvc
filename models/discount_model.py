from datetime import date
from decimal import Decimal

from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app_mvc.db.crud import Crud
from app_mvc.errors import AppError
from app_mvc.schemas.discount_schema import DiscountType


class DiscountNotFound(AppError):
    status_code = 404
    code = "discount_not_found"

    def __init__(self, discount_id: int) -> None:
        super().__init__(f"Descuento con ID {discount_id} no encontrado")


class DiscountServiceNotFound(AppError):
    status_code = 404
    code = "discount_service_not_found"

    def __init__(self, service_id: int) -> None:
        super().__init__(f"Servicio con ID {service_id} no encontrado")


class GossipDiscountAlreadyConfigured(AppError):
    status_code = 409
    code = "gossip_discount_already_configured"

    def __init__(self) -> None:
        super().__init__("Ya existe un descuento chisme configurado")


class DiscountModel:
    TABLE = "descuentos"
    SERVICE_TYPE = "servicio"
    GOSSIP_TYPE = "chisme"

    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        self.crud = Crud(connection)

    def list_all(self) -> list[dict]:
        rows = self.crud.select_all(self.TABLE)
        return [self._to_response(row) for row in rows]

    def list_public(self, today: date) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT d.id, d.nombre, d.tipo, d.porcentaje, d.servicio_id,
                   d.fecha_inicio, d.fecha_fin, d.activo
            FROM descuentos AS d
            JOIN servicios AS s ON s.id = d.servicio_id
            WHERE d.tipo = %s
              AND d.activo = TRUE
              AND s.activo = TRUE
              AND s.visible_online = TRUE
              AND (d.fecha_inicio IS NULL OR d.fecha_inicio <= %s)
              AND (d.fecha_fin IS NULL OR d.fecha_fin >= %s)
            ORDER BY d.id
            """,
            (self.SERVICE_TYPE, today, today),
        ).fetchall()
        return [self._to_response(row) for row in rows]

    def get(self, discount_id: int) -> dict:
        row = self.crud.select(self.TABLE, discount_id)
        if row is None:
            raise DiscountNotFound(discount_id)
        return self._to_response(row)

    def create(self, data: dict) -> dict:
        self._validate_service(data)
        try:
            row = self.crud.insert(self.TABLE, self._database_values(data))
        except UniqueViolation as error:
            self._raise_unique_conflict(error)
        except ForeignKeyViolation as error:
            raise DiscountServiceNotFound(data["service_id"]) from error
        return self._to_response(row)

    def update(self, discount_id: int, data: dict) -> dict:
        self._validate_service(data)
        try:
            row = self.crud.update(
                self.TABLE,
                discount_id,
                self._database_values(data, include_active=False),
            )
        except UniqueViolation as error:
            self._raise_unique_conflict(error)
        except ForeignKeyViolation as error:
            raise DiscountServiceNotFound(data["service_id"]) from error
        if row is None:
            raise DiscountNotFound(discount_id)
        return self._to_response(row)

    def deactivate(self, discount_id: int) -> dict:
        row = self.crud.update(self.TABLE, discount_id, {"activo": False})
        if row is None:
            raise DiscountNotFound(discount_id)
        return self._to_response(row)

    def _validate_service(self, data: dict) -> None:
        if self._discount_type(data) is DiscountType.SERVICE:
            service_id = data.get("service_id")
            if service_id is None or self.crud.select("servicios", service_id) is None:
                raise DiscountServiceNotFound(service_id or 0)

    @classmethod
    def _database_values(cls, data: dict, include_active: bool = True) -> dict:
        discount_type = cls._discount_type(data)
        values = {
            "nombre": data["name"],
            "tipo": (
                cls.SERVICE_TYPE
                if discount_type is DiscountType.SERVICE
                else cls.GOSSIP_TYPE
            ),
            "servicio_id": data.get("service_id"),
            "porcentaje": Decimal(str(data["percentage"])),
            "fecha_inicio": data.get("start_date"),
            "fecha_fin": data.get("end_date"),
        }
        if include_active:
            values["activo"] = True
        return values

    @staticmethod
    def _discount_type(data: dict) -> DiscountType:
        value = data["type"]
        if isinstance(value, DiscountType):
            return value
        return DiscountType(value)

    @classmethod
    def _to_response(cls, row: dict) -> dict:
        database_type = str(row["tipo"])
        return {
            "id": row["id"],
            "name": row["nombre"],
            "type": (
                DiscountType.SERVICE
                if database_type == cls.SERVICE_TYPE
                else DiscountType.GOSSIP
            ),
            "percentage": Decimal(str(row["porcentaje"])),
            "service_id": row["servicio_id"],
            "start_date": row["fecha_inicio"],
            "end_date": row["fecha_fin"],
            "is_active": row["activo"],
        }

    @staticmethod
    def _raise_unique_conflict(error: UniqueViolation) -> None:
        if error.diag.constraint_name == "uq_descuento_chisme":
            raise GossipDiscountAlreadyConfigured() from error
        raise error