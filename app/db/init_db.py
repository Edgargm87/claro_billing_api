# app/db/init_db.py

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """
    Crea las tablas si no existen.

    En un proyecto real de producción se recomienda usar migraciones (Alembic)
    en lugar de depender de create_all.
    """
    Base.metadata.create_all(bind=engine)
