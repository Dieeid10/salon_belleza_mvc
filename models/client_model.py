from psycopg import Connection
from psycopg.errors import UniqueViolation
from uuid import UUID

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
        self.connection = connection
        self.crud = Crud(connection)

    def get_or_create_for_appointment(
        self,
        first_name: str,
        last_name: str,
        phone: str,
    ) -> int:
        first_name = first_name.strip()
        last_name = last_name.strip()
        phone = phone.strip()

        # Serializa reservas concurrentes para el mismo teléfono.
        self.connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (phone,),
        )
        row = self.connection.execute(
            """
            SELECT id FROM clientes
            WHERE telefono = %s
            ORDER BY activo DESC, id
            LIMIT 1
            FOR UPDATE
            """,
            (phone,),
        ).fetchone()
        if row is not None:
            self.connection.execute(
                """
                UPDATE clientes
                SET nombre = %s, apellido = %s, activo = TRUE
                WHERE id = %s
                """,
                (first_name, last_name, row["id"]),
            )
            return row["id"]

        created = self.crud.insert(
            self.TABLE,
            {
                "nombre": first_name,
                "apellido": last_name,
                "telefono": phone,
            },
        )
        return created["id"]

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

    def get_or_create_for_appointment(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        *,
        guest_only: bool = False,
    ) -> int:
        
        first_name = first_name.strip()
        last_name = last_name.strip()
        phone = phone.strip()

        self.connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
            (phone,),
        )

        row = self.connection.execute(
            """
            SELECT id FROM clientes
            WHERE telefono = %s
              AND (NOT %s OR user_id IS NULL)
            ORDER BY activo DESC, id
            LIMIT 1
            FOR UPDATE
            """,
            (phone, guest_only),
        ).fetchone()

        if row is not None:
            if guest_only:
                return row["id"]

            self.connection.execute(
                """
                UPDATE clientes
                SET nombre = %s, apellido = %s, activo = TRUE
                WHERE id = %s
                """,
                (first_name, last_name, row["id"]),
            )
            return row["id"]

        created = self.crud.insert(
            self.TABLE,
            {
                "nombre": first_name,
                "apellido": last_name,
                "telefono": phone,
            },
        )
        return created["id"]

    def get_active_for_account(self, user_id: UUID) -> dict | None:
        return self.connection.execute(
            """
            SELECT id, telefono AS phone
            FROM public.clientes
            WHERE user_id = %s AND activo = TRUE
            FOR UPDATE
            """,
            (user_id,),
        ).fetchone()

    def set_booking_phone(self, client_id: int, phone: str) -> None:
        self.crud.update(self.TABLE, client_id, {"telefono": phone})

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