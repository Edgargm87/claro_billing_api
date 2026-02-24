# Placeholder for database initialisation logic
from app.db.base import Base
from app.db.session import engine

def init_db() -> None:
    # Base.metadata.create_all(bind=engine)
    pass
