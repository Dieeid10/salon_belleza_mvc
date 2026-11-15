from fastapi import APIRouter, Depends, status

from app_mvc.controllers.auth_controller import AuthController
from app_mvc.models.auth_model import AuthModel
from app_mvc.responses import success_response
from app_mvc.schemas.auth_schema import LoginRequest, RefreshRequest

router = APIRouter()


def get_auth_controller() -> AuthController:
    """Construye el controller y su modelo para atender la petición."""
    return AuthController(AuthModel())


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    body: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    print('los datos que llegan al login son: ', body)
    tokens = controller.login(body.email, body.password)
    return success_response(tokens, "Inicio de sesión exitoso")


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(
    body: RefreshRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    tokens = controller.refresh(body.refresh_token)
    return success_response(tokens, "Sesión renovada")