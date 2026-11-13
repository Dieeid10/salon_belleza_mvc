from fastapi import APIRouter
from app.routes.auth_route import router as auth_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Autenticación"])

