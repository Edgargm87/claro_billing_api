# app/services/auth_service.py

from datetime import timedelta
from typing import Optional

from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import (
    crear_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.schemas.auth import Token

# Usuario "fake" para la plantilla.
# En un proyecto real esto saldría de la BD.
FAKE_USER_DB = {
    "demo": {
        "username": "demo",
        "password": "secret",   # en prod: hasheado
        "roles": ["admin"],
    }
}


def autenticar_usuario(form_data: OAuth2PasswordRequestForm) -> Optional[Token]:
    """
    Valida credenciales y genera un token en caso correcto.
    """
    username = form_data.username
    password = form_data.password

    user = FAKE_USER_DB.get(username)
    if not user or user["password"] != password:
        return None

    roles = user.get("roles", [])
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = crear_access_token(
        data={"sub": username, "roles": roles},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")
