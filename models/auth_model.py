from app_mvc.errors import AppError
from app_mvc.config.config import settings
import httpx

class CredentialsInvalid(AppError):
    """Las credenciales proporcionadas son inválidas."""

    status_code = 401
    code = "invalid_credentials"

    def __init__(self, message: str = "Credenciales inválidas") -> None:
        super().__init__(message)

class AuthModel:
    def _get_token(self, type: str, data: dict) -> dict:
        response = httpx.post(
            f"{settings.supabase_url}/auth/v1/token",
            params={"grant_type": type},
            headers={"apikey": settings.supabase_anon_key},
            json=data,
            timeout=10
        )

        if response.is_error:
            print("Estado:", response.status_code)
            print("Detalle:", response.text)

        if response.status_code in (400, 401):
            raise CredentialsInvalid("Credenciales inválidas")

        response.raise_for_status()
        return response.json()

    def login(self, email: str, password: str) -> dict:
        return self._get_token("password", {"email": email, "password": password})

    def refresh(self, refresh_token: str) -> dict:
        return self._get_token("refresh_token", {"refresh_token": refresh_token})