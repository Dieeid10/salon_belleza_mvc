from uuid import UUID

from fastapi import APIRouter, Depends, status
from psycopg import Connection

from app_mvc.controllers.staff_controller import StaffController
from app_mvc.db.database import get_db_connection
from app_mvc.models.staff_profile_model import StaffProfileModel
from app_mvc.models.supabase_admin_model import SupabaseAdminModel
from app_mvc.responses import success_response
from app_mvc.schemas.staff_schema import InviteSellerRequest, StaffInvitationResponse, StaffResponse
from app_mvc.security import require_role

router = APIRouter(dependencies=[Depends(require_role("dueno"))])


def get_staff_controller(connection: Connection = Depends(get_db_connection)) -> StaffController:
    return StaffController(
        profiles=StaffProfileModel(connection),
        auth_admin=SupabaseAdminModel(),
    )


@router.get("/")
def list_staff(
    controller: StaffController = Depends(get_staff_controller),
):
    staff = [
        StaffResponse.model_validate(person).model_dump(mode="json")
        for person in controller.list_staff()
    ]
    return success_response(staff, "Personal obtenido correctamente")


@router.post("/", status_code=status.HTTP_201_CREATED)
def invite_seller(
    body: InviteSellerRequest,
    controller: StaffController = Depends(get_staff_controller),
):
    seller = StaffInvitationResponse.model_validate(
        controller.invite_seller(body.name, str(body.email))
    ).model_dump(mode="json")
    return success_response(
        seller,
        "Invitación enviada al vendedor",
        status.HTTP_201_CREATED,
    )


@router.delete("/{user_id}")
def remove_seller(
    user_id: UUID,
    controller: StaffController = Depends(get_staff_controller),
):
    controller.remove_seller(user_id)
    return success_response(None, "Acceso del vendedor eliminado")