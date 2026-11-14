from fastapi import APIRouter, Depends, Query, status
from psycopg import Connection

from app_mvc.controllers.client_controller import ClientController
from app_mvc.db.database import get_db_connection
from app_mvc.models.client_model import ClientModel
from app_mvc.responses import success_response
from app_mvc.schemas.client_schema import ClientRequest, ClientResponse
from app_mvc.security import require_role

router = APIRouter(
    dependencies=[Depends(require_role("dueno", "vendedor"))],
)

def get_client_controller(
    connection: Connection = Depends(get_db_connection),
) -> ClientController:
    """Entrega un controller con su modelo conectado a la base de datos."""
    model = ClientModel(connection)
    return ClientController(model)

def response_client(row: dict) -> dict:
    """Traduce los nombres de columnas de PostgreSQL al contrato HTTP."""
    client = {
        "id": row["id"],
        "first_name": row["nombre"],
        "last_name": row["apellido"],
        "phone": row["telefono"],
        "email": row["email"],
        "is_active": row["activo"],
        "created_at": row["fecha_creacion"],
    }
    return ClientResponse.model_validate(client).model_dump(mode="json")

@router.get("/")
def list_clients(
    only_active: bool = Query(True, description="Filtrar solo clientes activos"),
    controller: ClientController = Depends(get_client_controller),
):
    """Lista todos los clientes, con opción de filtrar solo los activos."""
    clients = controller.list_clients(only_active)
    return success_response(
        [response_client(client) for client in clients],
        "Clientes obtenidos correctamente",
    )

@router.get("/{client_id}")
def get_client(
    client_id: int,
    controller: ClientController = Depends(get_client_controller),
):
    """Obtiene un cliente por su ID."""
    return success_response(
        response_client(controller.get_client(client_id)),
        "Cliente obtenido correctamente",
    )

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientRequest,
    controller: ClientController = Depends(get_client_controller),
):
    """Crea un nuevo cliente."""
    return success_response(
        response_client(controller.create_client(body.model_dump())),
        "Cliente creado correctamente",
    )

@router.put("/{client_id}")
def update_client(
    client_id: int,
    body: ClientRequest,
    controller: ClientController = Depends(get_client_controller),
):
    """Actualiza un cliente existente."""
    return success_response(
        response_client(controller.update_client(client_id, body.model_dump())),
        "Cliente actualizado correctamente",
    )

@router.patch("/{client_id}/activate")
def activate_client(
    client_id: int,
    controller: ClientController = Depends(get_client_controller),
):
    """Activa un cliente existente."""
    return success_response(
        response_client(controller.activate_client(client_id)),
        "Cliente activado correctamente",
    )

@router.delete("/{client_id}")
def deactivate_client(
    client_id: int,
    controller: ClientController = Depends(get_client_controller),
):
    """Desactiva un cliente existente."""
    return success_response(
        response_client(controller.deactivate_client(client_id)),
        "Cliente desactivado correctamente",
    )