# app/core/config.py

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuración central de la app.

    Lee valores desde variables de entorno y/o archivo .env.
    """
    secret_key: str
    database_url: str = "sqlite:///./service.db"
    access_token_expire_minutes: int = 30
    
    # Orígenes CORS permitidos (string separada por comas o '*')
    cors_allow_origins: str = "*"   # por defecto: todos (desarrollo)


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """
    Usamos lru_cache para que Settings se instancie una sola vez
    (pattern recomendado por la propia doc de FastAPI).
    """
    return Settings()


# Instancia global cómoda para importar directamente
settings = get_settings()
