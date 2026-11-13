from fastapi import APIRouter
from app_mvc.routes.auth_route import router as auth_router
from app_mvc.routes.client_route import router as client_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
router.include_router(client_router, prefix="/clients", tags=["Clientes"])
