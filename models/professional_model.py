from psycopg import Connection

from app_mvc.db.crud import Crud
from app_mvc.errors import AppError


class ProfessionalNotFound(AppError):
    status_code = 404
    code = "professional_not_found"

    def __init__(self, professional_id: int) -> None:
        super().__init__(f"Profesional con ID {professional_id} no encontrado")


class ProfessionalModel:
    TABLE = "profesionales"

    def __init__(self, connection: Connection) -> None:
        self.crud = Crud(connection)

    def list_all(self, only_active: bool = True) -> list[dict]:
        if only_active:
            rows = self.crud.select_all(self.TABLE, "activo = %s", (True,))
        else:
            rows = self.crud.select_all(self.TABLE)
        return sorted(rows, key=lambda row: row["id"])

    def get(self, professional_id: int) -> dict:
        row = self.crud.select(self.TABLE, professional_id)
        if row is None:
            raise ProfessionalNotFound(professional_id)
        return row

    def create(self, data: dict) -> dict:
        return self.crud.insert(
            self.TABLE,
            {
                "nombre": data["name"],
                "perfil_id": data.get("profile_id"),
                "activo": True,
            },
        )

    def update(self, professional_id: int, data: dict) -> dict:
        row = self.crud.update(
            self.TABLE,
            professional_id,
            {
                "nombre": data["name"],
                "perfil_id": data.get("profile_id"),
            },
        )
        if row is None:
            raise ProfessionalNotFound(professional_id)
        return row

    def deactivate(self, professional_id: int) -> dict:
        row = self.crud.update(
            self.TABLE,
            professional_id,
            {"activo": False},
        )
        if row is None:
            raise ProfessionalNotFound(professional_id)
        return row