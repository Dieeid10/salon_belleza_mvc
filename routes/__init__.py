from fastapi import APIRouter
from app_mvc.routes.auth_route import router as auth_router
from app_mvc.routes.client_route import router as client_router
from app_mvc.routes.professional_route import router as professional_router
from app_mvc.routes.service_route import router as service_router
from app_mvc.routes.discount_route import router as discount_router
from app_mvc.routes.sale_route import router as sale_router
from app_mvc.routes.appointment_route import admin_router as appointment_admin_router
from app_mvc.routes.appointment_route import public_router as appointment_public_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
router.include_router(client_router, prefix="/clients", tags=["Clientes"])
router.include_router(professional_router, prefix="/professionals", tags=["Profesionales"])
router.include_router(service_router, prefix="/services", tags=["Servicios"])
router.include_router(discount_router, prefix="/discounts", tags=["Descuentos"])
router.include_router(sale_router, prefix="/sales", tags=["Ventas"])
router.include_router(
	appointment_public_router,
	prefix="/appointments",
	tags=["Turnos públicos"],
)
router.include_router(
	appointment_admin_router,
	prefix="/admin/appointments",
	tags=["Gestión de turnos"],
)
