# app/db/session.py


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Lee la URL de la base de datos desde la configuración
DATABASE_URL = settings.database_url

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # Necesario para SQLite en modo single-thread (FastAPI dev)
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependencia de FastAPI para obtener una sesión de BD por request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
