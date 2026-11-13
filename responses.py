import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.errors import AppError

logger = logging.getLogger(__name__)


def success_response(
    data: Any,
    message: str = "Operación exitosa",
    status_code: int = 200,
) -> JSONResponse:
    """Construye una respuesta exitosa con el formato común de la API."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": jsonable_encoder(data),
            "errors": None,
        },
    )


def _error_response(
    status_code: int,
    message: str,
    errors: Any = None,
    code: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "errors": jsonable_encoder(errors),
            "code": code,
        },
    )


async def handle_app_error(_: Request, error: AppError) -> JSONResponse:
    return _error_response(
        error.status_code,
        error.message,
        code=error.code,
    )


async def handle_http_error(_: Request, error: HTTPException) -> JSONResponse:
    detail = error.detail
    message = detail if isinstance(detail, str) else "La solicitud no pudo completarse"
    errors = None if isinstance(detail, str) else detail
    return _error_response(error.status_code, message, errors, "http_error")


async def handle_validation_error(
    _: Request,
    error: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        422,
        "Los datos enviados no son válidos",
        error.errors(),
        "validation_error",
    )


async def handle_unexpected_error(_: Request, error: Exception) -> JSONResponse:
    logger.exception("Error inesperado al procesar la solicitud", exc_info=error)
    return _error_response(
        500,
        "Ocurrió un error interno",
        code="internal_error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra el formato común para errores de aplicación, HTTP y validación."""
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(HTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)