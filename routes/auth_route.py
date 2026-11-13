from fastapi import APIRouter, Depends, status

from app.controllers.auth_controller import AuthController
from app.models.auth_model import AuthModel
from app.responses import success_response
from app.schemas.auth_schema import LoginRequest, RefreshRequest

router = APIRouter()


def get_auth_controller() -> AuthController:
    """Construye el controller y su modelo para atender la petición."""
    return AuthController(AuthModel())


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    body: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    tokens = controller.login(body.email, body.password)
    return success_response(tokens, "Inicio de sesión exitoso")


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(
    body: RefreshRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    tokens = controller.refresh(body.refresh_token)
    return success_response(tokens, "Sesión renovada")