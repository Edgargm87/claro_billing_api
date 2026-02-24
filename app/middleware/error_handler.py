# app/middleware/error_handler.py

from fastapi import Request
from fastapi.responses import JSONResponse


async def global_error_handler(request: Request, call_next):
    """
    Middleware global para capturar errores no manejados y devolver
    una respuesta JSON estándar.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        # Aquí podrías loguear el error con logging o Sentry
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "Error interno del servidor",
                    "detail": str(exc),
                }
            },
        )
