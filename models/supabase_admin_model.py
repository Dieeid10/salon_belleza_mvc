from typing import Any
from uuid import UUID

import httpx

from app_mvc.config.config import settings
from app_mvc.exceptions.staff import (
    StaffAuthProviderError,
    StaffEmailAlreadyRegistered,
    StaffManagementNotConfigured,
)


class SupabaseAdminModel:
    """Operaciones administrativas de Supabase Auth, solo desde el backend."""

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        key = settings.supabase_service_role_key
        if not key:
            raise StaffManagementNotConfigured()

        try:
            response = httpx.request(
                method,
                f"{settings.supabase_url.rstrip('/')}/auth/v1{path}",
                params=params,
                headers={"apikey": key, "Authorization": f"Bearer {key}"},
                json=json,
                timeout=15,
            )
        except httpx.RequestError as error:
            raise StaffAuthProviderError() from error

        if response.status_code in (400, 409, 422):
            raise StaffEmailAlreadyRegistered()
        if not response.is_success:
            raise StaffAuthProviderError()
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def invite_seller(self, email: str, name: str) -> dict:
        params = {}
        if settings.supabase_invite_redirect_url:
            params["redirect_to"] = settings.supabase_invite_redirect_url
        result = self._request(
            "POST",
            "/invite",
            params=params,
            json={"email": email, "data": {"full_name": name}},
        )
        user = result.get("user", result) if isinstance(result, dict) else {}
        try:
            return {"id": UUID(str(user["id"])), "email": user["email"]}
        except (KeyError, TypeError, ValueError) as error:
            raise StaffAuthProviderError() from error

    def list_users(self) -> list[dict]:
        users: list[dict] = []
        page = 1
        per_page = 100
        while True:
            result = self._request(
                "GET",
                "/admin/users",
                params={"page": page, "per_page": per_page},
            )
            page_users = result.get("users", []) if isinstance(result, dict) else result
            if not isinstance(page_users, list):
                raise StaffAuthProviderError()
            users.extend(page_users)
            if len(page_users) < per_page:
                return users
            page += 1

    def delete_user(self, user_id: UUID) -> None:
        self._request("DELETE", f"/admin/users/{user_id}")