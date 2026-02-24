# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes_health import router as health_router
from app.api.v1.routes_auth import router as auth_router
from app.db.init_db import init_db
from app.middleware.error_handler import global_error_handler

from app.api.v1 import __init__ as api_v1  # solo para que no quede "muerto" el paquete

def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Service Template")

    # Inicializar BD (crea tablas si no existen)
    init_db()

    # Implementar CORS
    if settings.cors_allow_origins == "*":
        origins = ["*"]
    else:
        origins = [
            o.strip()
            for o in settings.cors_allow_origins.split(",")
            if o.strip()
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],    # puedes restringir en prod si quieres
        allow_headers=["*"],
    )


    # Middlewares
    app.middleware("http")(global_error_handler)

    # Routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")

    return app


app = create_app()

