# app/schemas/auth.py

from pydantic import BaseModel


class Token(BaseModel):
    """
    Respuesta estándar de login.
    """
    access_token: str
    token_type: str = "bearer"
