from uuid import UUID

from psycopg import Connection

from app_mvc.db.crud import Crud


class StaffProfileModel:
    TABLE = "perfiles"

    def __init__(self, connection: Connection) -> None:
        self.crud = Crud(connection)

    def list_all(self) -> list[dict]:
        rows = self.crud.select_all(self.TABLE)
        return [self._to_staff(row) for row in rows]

    def get(self, user_id: UUID) -> dict | None:
        row = self.crud.select(self.TABLE, user_id)
        return self._to_staff(row) if row is not None else None

    def create_seller(self, user_id: UUID, name: str) -> dict:
        row = self.crud.insert(
            self.TABLE,
            {
                "id": user_id,
                "nombre": name,
                "rol": "vendedor",
            },
        )
        return self._to_staff(row)

    @staticmethod
    def _to_staff(row: dict) -> dict:
        return {
            "id": row["id"],
            "name": row["nombre"],
            "role": str(row["rol"]),
            "created_at": row["fecha_creacion"],
        }