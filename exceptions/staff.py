from app_mvc.errors import AppError


class StaffManagementNotConfigured(AppError):
    status_code = 503
    code = "staff_management_not_configured"

    def __init__(self) -> None:
        super().__init__("La gestión de usuarios no está configurada")


class StaffEmailAlreadyRegistered(AppError):
    status_code = 409
    code = "staff_email_already_registered"

    def __init__(self) -> None:
        super().__init__("Ese email ya está registrado en Supabase Auth")


class StaffUserNotFound(AppError):
    status_code = 404
    code = "staff_user_not_found"

    def __init__(self) -> None:
        super().__init__("No se encontró el usuario de personal")


class StaffUserNotSeller(AppError):
    status_code = 403
    code = "staff_user_not_seller"

    def __init__(self) -> None:
        super().__init__("Solo se puede retirar el acceso de un vendedor")


class StaffAuthProviderError(AppError):
    status_code = 502
    code = "staff_auth_provider_error"

    def __init__(self) -> None:
        super().__init__("Supabase no pudo completar la gestión del usuario")


class StaffProfileProvisionFailed(AppError):
    status_code = 500
    code = "staff_profile_provision_failed"

    def __init__(self) -> None:
        super().__init__("No se pudo crear el perfil del vendedor")