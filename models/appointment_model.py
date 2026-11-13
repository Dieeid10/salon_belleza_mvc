from datetime import date, datetime, time, timedelta, timezone, tzinfo
from decimal import Decimal

from psycopg import Connection
from psycopg.errors import ExclusionViolation

from app_mvc.db.crud import Crud
from app_mvc.exceptions.appointments import (
    AppointmentInPast,
    AppointmentNotFound,
    AppointmentNotStarted,
    InvalidStatusTransition,
    TimeSlotUnavailable,
)
from app_mvc.schemas.appointment_schema import AppointmentStatus


STATUS_TO_DATABASE = {
    AppointmentStatus.PENDING: "Pendiente",
    AppointmentStatus.CONFIRMED: "Confirmado",
    AppointmentStatus.COMPLETED: "Realizado",
    AppointmentStatus.CANCELLED: "Cancelado",
    AppointmentStatus.ABSENT: "Ausente",
}
DATABASE_TO_STATUS = {
    database_value: status for status, database_value in STATUS_TO_DATABASE.items()
}
ACTIVE_DATABASE_STATUSES = ["Pendiente", "Confirmado"]
ALLOWED_TRANSITIONS = {
    AppointmentStatus.PENDING: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.ABSENT,
    },
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.ABSENT: set(),
}


class AppointmentModel:
    """Recupera turnos y aplica sus reglas de agenda y transición de estado."""

    TABLE = "turnos"
    DETAIL_TABLE = "detalle_turnos"

    def __init__(
        self,
        connection: Connection,
        salon_timezone: tzinfo = timezone.utc,
    ) -> None:
        self.connection = connection
        self.crud = Crud(connection)
        self.salon_timezone = salon_timezone

    def schedule_for(self, professional_id: int, day: date) -> list[tuple[datetime, datetime]]:
        weekday = (day.weekday() + 1) % 7
        rows = self.connection.execute(
            """
            SELECT hora_apertura, hora_cierre
            FROM horarios_atencion
            WHERE profesional_id = %s AND dia_semana = %s AND activo = TRUE
            ORDER BY hora_apertura
            """,
            (professional_id, weekday),
        ).fetchall()
        return [
            (
                datetime.combine(day, row["hora_apertura"], self.salon_timezone),
                datetime.combine(day, row["hora_cierre"], self.salon_timezone),
            )
            for row in rows
        ]

    def occupied_slots(
        self,
        professional_id: int,
        starts_at: datetime,
        ends_at: datetime,
    ) -> list[tuple[datetime, datetime]]:
        appointments = self.connection.execute(
            """
            SELECT fecha_hora AS starts_at, fecha_hora_fin AS ends_at
            FROM turnos
            WHERE profesional_id = %s
              AND estado::text = ANY(%s)
              AND fecha_hora < %s
              AND fecha_hora_fin > %s
            """,
            (professional_id, ACTIVE_DATABASE_STATUSES, ends_at, starts_at),
        ).fetchall()
        blocks = self.connection.execute(
            """
            SELECT fecha_inicio AS starts_at, fecha_fin AS ends_at
            FROM bloqueos
            WHERE (profesional_id IS NULL OR profesional_id = %s)
              AND fecha_inicio < %s
              AND fecha_fin > %s
            """,
            (professional_id, ends_at, starts_at),
        ).fetchall()
        return [
            (row["starts_at"], row["ends_at"])
            for row in [*appointments, *blocks]
        ]

    @staticmethod
    def is_available(
        starts_at: datetime,
        ends_at: datetime,
        schedule: list[tuple[datetime, datetime]],
        occupied: list[tuple[datetime, datetime]],
    ) -> bool:
        fits_working_hours = any(
            opening <= starts_at and ends_at <= closing
            for opening, closing in schedule
        )
        does_not_overlap = not any(
            starts_at < busy_end and busy_start < ends_at
            for busy_start, busy_end in occupied
        )
        return fits_working_hours and does_not_overlap

    @classmethod
    def available_starts(
        cls,
        schedule: list[tuple[datetime, datetime]],
        occupied: list[tuple[datetime, datetime]],
        duration: timedelta,
        now: datetime,
        step: timedelta = timedelta(minutes=15),
    ) -> list[datetime]:
        starts: list[datetime] = []
        for opening, closing in schedule:
            candidate_start = opening
            while candidate_start + duration <= closing:
                candidate_end = candidate_start + duration
                if candidate_start > now and cls.is_available(
                    candidate_start,
                    candidate_end,
                    [(opening, closing)],
                    occupied,
                ):
                    starts.append(candidate_start)
                candidate_start += step
        return starts

    def create(
        self,
        client_id: int,
        professional_id: int,
        starts_at: datetime,
        ends_at: datetime,
        services: list[dict],
    ) -> dict:
        try:
            appointment = self.crud.insert(
                self.TABLE,
                {
                    "cliente_id": client_id,
                    "profesional_id": professional_id,
                    "fecha_hora": starts_at,
                    "fecha_hora_fin": ends_at,
                },
            )
        except ExclusionViolation as error:
            raise TimeSlotUnavailable() from error

        for service in services:
            self.crud.insert(
                self.DETAIL_TABLE,
                {
                    "turno_id": appointment["id"],
                    "servicio_id": service["id"],
                    "precio_lista": service["price"],
                    "descuento_pct": Decimal("0"),
                    "precio_reservado": service["price"],
                },
            )
        return self.get(appointment["id"])

    def get(self, appointment_id: int, lock: bool = False) -> dict:
        lock_clause = " FOR UPDATE" if lock else ""
        row = self.connection.execute(
            f"SELECT * FROM turnos WHERE id = %s{lock_clause}",
            (appointment_id,),
        ).fetchone()
        if row is None:
            raise AppointmentNotFound(appointment_id)
        return self._to_response(
            row,
            self._load_details([appointment_id]).get(appointment_id, []),
        )

    def list_all(
        self,
        starts_at: datetime,
        ends_at: datetime,
        professional_id: int | None = None,
        status: AppointmentStatus | None = None,
    ) -> list[dict]:
        conditions = ["fecha_hora >= %s", "fecha_hora < %s"]
        parameters: list = [starts_at, ends_at]
        if professional_id is not None:
            conditions.append("profesional_id = %s")
            parameters.append(professional_id)
        if status is not None:
            conditions.append("estado::text = %s")
            parameters.append(STATUS_TO_DATABASE[status])

        rows = self.connection.execute(
            f"SELECT * FROM turnos WHERE {' AND '.join(conditions)} ORDER BY fecha_hora",
            parameters,
        ).fetchall()
        details = self._load_details([row["id"] for row in rows])
        return [
            self._to_response(row, details.get(row["id"], []))
            for row in rows
        ]

    def change_status(
        self,
        appointment_id: int,
        requested_status: AppointmentStatus,
        now: datetime,
    ) -> dict:
        row = self.connection.execute(
            "SELECT id, estado, fecha_hora FROM turnos WHERE id = %s FOR UPDATE",
            (appointment_id,),
        ).fetchone()
        if row is None:
            raise AppointmentNotFound(appointment_id)

        current_status = DATABASE_TO_STATUS[str(row["estado"])]
        if requested_status not in ALLOWED_TRANSITIONS[current_status]:
            raise InvalidStatusTransition(
                current_status.value,
                requested_status.value,
            )
        if (
            requested_status in (AppointmentStatus.COMPLETED, AppointmentStatus.ABSENT)
            and now < row["fecha_hora"]
        ):
            raise AppointmentNotStarted()

        self.connection.execute(
            "UPDATE turnos SET estado = %s::estado_turno WHERE id = %s",
            (STATUS_TO_DATABASE[requested_status], appointment_id),
        )
        return self.get(appointment_id)

    def cancel(self, appointment_id: int, now: datetime) -> dict:
        return self.change_status(appointment_id, AppointmentStatus.CANCELLED, now)

    def _load_details(self, appointment_ids: list[int]) -> dict[int, list[dict]]:
        if not appointment_ids:
            return {}
        rows = self.connection.execute(
            """
            SELECT d.turno_id, d.servicio_id, s.nombre_servicio,
                   s.duracion_minutos, d.precio_reservado
            FROM detalle_turnos AS d
            JOIN servicios AS s ON s.id = d.servicio_id
            WHERE d.turno_id = ANY(%s)
            ORDER BY d.turno_id, d.id
            """,
            (appointment_ids,),
        ).fetchall()
        details: dict[int, list[dict]] = {}
        for row in rows:
            details.setdefault(row["turno_id"], []).append(
                {
                    "service_id": row["servicio_id"],
                    "name": row["nombre_servicio"],
                    "duration_minutes": row["duracion_minutos"],
                    "price": Decimal(str(row["precio_reservado"])),
                }
            )
        return details

    @staticmethod
    def _to_response(row: dict, details: list[dict]) -> dict:
        status = DATABASE_TO_STATUS[str(row["estado"])]
        return {
            "id": row["id"],
            "client_id": row["cliente_id"],
            "professional_id": row["profesional_id"],
            "starts_at": row["fecha_hora"],
            "ends_at": row["fecha_hora_fin"],
            "status": status,
            "total": sum(
                (detail["price"] for detail in details),
                Decimal("0.00"),
            ),
            "details": details,
        }

    def get_for_sale(self, appointment_id: int) -> dict | None:
        row = self.connection.execute(
            """
            SELECT id, cliente_id, estado
            FROM turnos
            WHERE id = %s
            FOR UPDATE
            """,
            (appointment_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "client_id": row["cliente_id"],
            "status": str(row["estado"]),
        }

    def get_details_for_sale(self, appointment_id: int) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT servicio_id, descuento_id, precio_lista,
                   descuento_pct, precio_reservado
            FROM detalle_turnos
            WHERE turno_id = %s
            ORDER BY id
            """,
            (appointment_id,),
        ).fetchall()
        return [
            {
                "service_id": row["servicio_id"],
                "discount_id": row["descuento_id"],
                "list_price": row["precio_lista"],
                "service_discount_percentage": row["descuento_pct"],
                "reserved_price": row["precio_reservado"],
            }
            for row in rows
        ]