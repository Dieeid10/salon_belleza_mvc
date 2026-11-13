from psycopg import Connection
from psycopg.errors import UniqueViolation

from app_mvc.db.crud import Crud
from app_mvc.errors import AppError

class ClientNotFound(AppError):
    status_code = 404
    code = "client_not_found"

    def __init__(self, client_id: int) -> None:
        super().__init__(f"Cliente con ID {client_id} no encontrado")

class ClientEmailConflict(AppError):
    status_code = 409
    code = "client_email_conflict"

    def __init__(self, email: str) -> None:
        super().__init__(f"El correo electrónico '{email}' ya está en uso por otro cliente")

class ClientModel:
    """modelo de cliente que interactúa con la base de datos usando Psycopg."""

    TABLE = "clientes"

    def __init__(self, connection: Connection):
        self.crud = Crud(connection)

    def list_all(self, only_active: bool = True) -> list[dict]:
        """Devuelve todos los clientes en la base de datos."""
        if only_active:
            rows = self.crud.select_all(self.TABLE, "activo = %s", (True,))
        else:
            rows = self.crud.select_all(self.TABLE)
        return sorted(rows, key=lambda row: row["id"])

    def get(self, client_id: int) -> dict:
        """Devuelve un cliente por su ID o lanza ClientNotFound si no existe."""
        row = self.crud.select(self.TABLE, client_id)
        if row is None:
            raise ClientNotFound(client_id)
        return row

    def create(self, client_data: dict) -> dict:
        """Crea un nuevo cliente en la base de datos y devuelve sus datos."""
        try:
            return self.crud.insert(self.TABLE, self._datos_db(client_data))
        except UniqueViolation as error:
            if error.diag.constrait_name == "uq_clientes_email":
                raise ClientEmailConflict(client_data["email"]) from error
            raise

    def update(self, client_id: int, client_data: dict) -> dict:
        """Actualiza un cliente existente y devuelve sus datos actualizados."""
        try:
            updated_row = self.crud.update(
                self.TABLE, client_id, self._datos_db(client_data)
            )
            if updated_row is None:
                raise ClientNotFound(client_id)
            return updated_row
        except UniqueViolation as error:
            if error.diag.constraint_name == "uq_clientes_email":
                raise ClientEmailConflict(client_data["email"]) from error
            raise

    def change_status(self, client_id: int, is_active: bool) -> dict:
        """Cambia el estado activo de un cliente y devuelve sus datos actualizados."""
        updated_row = self.crud.update(
            self.TABLE, client_id, {"activo": is_active}
        )
        if updated_row is None:
            raise ClientNotFound(client_id)
        return updated_row

    @staticmethod
    def _datos_db(client_data: dict) -> dict:
        """Convierte los datos de entrada a un formato adecuado para la base de datos."""
        return {
            "nombre": client_data["first_name"],
            "apellido": client_data["last_name"],
            "telefono": client_data.get("phone"),
            "email": client_data.get("email"),
            "activo": True,
        }