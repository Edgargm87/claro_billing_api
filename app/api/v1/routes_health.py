# app/api/v1/routes_health.py

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Endpoint sencillo para verificar que el servicio está vivo.
    Ideal para Kubernetes, load balancers, etc.
    """
    return {"status": "ok"}
