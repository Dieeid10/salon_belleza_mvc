from decimal import Decimal

from psycopg import Connection
from app_mvc.db.crud import Crud
from app_mvc.errors import AppError


class ServiceNotFound(AppError):
    status_code = 404
    code = "service_not_found"

    def __init__(self, service_id: int) -> None:
        super().__init__(f"Servicio con ID {service_id} no encontrado")


class ServiceModel:
    TABLE = "servicios"

    def __init__(self, connection: Connection) -> None:
        self.crud = Crud(connection)

    def list_all(
        self,
        only_active: bool = True,
        only_online: bool = True,
    ) -> list[dict]:
        conditions = []
        parameters = []
        if only_active:
            conditions.append("activo = %s")
            parameters.append(True)
        if only_online:
            conditions.append("visible_online = %s")
            parameters.append(True)

        return self.crud.select_all(
            self.TABLE,
            " AND ".join(conditions) if conditions else None,
            tuple(parameters),
        )

    def get(self, service_id: int) -> dict:
        row = self.crud.select(self.TABLE, service_id)
        if row is None:
            raise ServiceNotFound(service_id)
        return row

    def get_public(self, service_id: int) -> dict:
        row = self.get(service_id)
        if not row["activo"] or not row["visible_online"]:
            raise ServiceNotFound(service_id)
        return row

    def create(self, data: dict) -> dict:
        return self.crud.insert(self.TABLE, self._database_values(data))

    def update(self, service_id: int, data: dict) -> dict:
        row = self.crud.update(
            self.TABLE,
            service_id,
            self._database_values(data, include_active=False),
        )
        if row is None:
            raise ServiceNotFound(service_id)
        return row

    def deactivate(self, service_id: int) -> dict:
        row = self.crud.update(self.TABLE, service_id, {"activo": False})
        if row is None:
            raise ServiceNotFound(service_id)
        return row

    @staticmethod
    def _database_values(data: dict, include_active: bool = True) -> dict:
        values = {
            "nombre_servicio": data["name"],
            "descripcion": data.get("description"),
            "precio": Decimal(str(data["price"])),
            "duracion_minutos": data["duration_minutes"],
            "visible_online": data["visible_online"],
        }
        if include_active:
            values["activo"] = True
        return values