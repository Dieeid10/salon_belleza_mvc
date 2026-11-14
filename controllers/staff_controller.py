import logging
from uuid import UUID

from app_mvc.exceptions.staff import (
    StaffProfileProvisionFailed,
    StaffUserNotFound,
    StaffUserNotSeller,
)
from app_mvc.models.staff_profile_model import StaffProfileModel
from app_mvc.models.supabase_admin_model import SupabaseAdminModel

logger = logging.getLogger(__name__)


class StaffController:
    """Coordina la administración de cuentas de personal y sus perfiles."""

    def __init__(
        self,
        profiles: StaffProfileModel,
        auth_admin: SupabaseAdminModel,
    ) -> None:
        self.profiles = profiles
        self.auth_admin = auth_admin

    def list_staff(self) -> list[dict]:
        users_by_id = {
            str(user["id"]): user
            for user in self.auth_admin.list_users()
            if user.get("id") is not None
        }
        staff = []
        for profile in self.profiles.list_all():
            user = users_by_id.get(str(profile["id"]), {})
            staff.append({**profile, "email": user.get("email")})
        return staff

    def invite_seller(self, name: str, email: str) -> dict:
        user = self.auth_admin.invite_seller(email, name)
        try:
            profile = self.profiles.create_seller(user["id"], name)
        except Exception as error:
            try:
                self.auth_admin.delete_user(user["id"])
            except Exception:
                logger.exception(
                    "Falló la limpieza de una cuenta Auth sin perfil asociado"
                )
            raise StaffProfileProvisionFailed() from error
        return {**profile, "email": user["email"]}

    def remove_seller(self, user_id: UUID) -> None:
        profile = self.profiles.get(user_id)
        if profile is None:
            raise StaffUserNotFound()
        if profile["role"] != "vendedor":
            raise StaffUserNotSeller()
        # La FK perfiles.id -> auth.users.id elimina el perfil en cascada.
        self.auth_admin.delete_user(user_id)