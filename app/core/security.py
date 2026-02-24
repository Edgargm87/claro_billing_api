# app/core/security.py

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from app.core.config import settings

# Lee valores de configuracion
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Ruta donde se obtiene el token (la implementamos en routes_auth)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


class TokenData(BaseModel):
    """
    Información mínima que necesitamos del usuario autenticado.
    Se rellena a partir del JWT.
    """
    username: Optional[str] = None
    roles: List[str] = []


def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un JWT firmado con SECRET_KEY.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.
    Lanza JWTError si hay problemas (firma, expiración, etc.).
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Dependencia que:
    - extrae el token del header Authorization: Bearer ...
    - lo valida
    - devuelve un TokenData con username y roles.
    """
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        username: Optional[str] = payload.get("sub")
        roles: List[str] = payload.get("roles", [])

        if username is None:
            raise cred_exc

        return TokenData(username=username, roles=roles)

    except JWTError:
        raise cred_exc


# 🔒 Roles y permisos básicos (puedes extender esto en cada servicio)
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": ["*"],           # '*' -> todos los permisos
    "user": ["items:read"],   # ejemplo
}


def get_permissions_from_roles(roles: list[str]) -> list[str]:
    """
    A partir de una lista de roles, devuelve la lista de permisos efectivos.
    Si algún rol tiene '*', se interpreta como "todos los permisos".
    """
    permisos: set[str] = set()
    for role in roles:
        role_perms = ROLE_PERMISSIONS.get(role, [])
        if "*" in role_perms:
            return ["*"]
        permisos.update(role_perms)
    return list(permisos)


def require_role(required_role: str):
    """
    Dependencia que exige que el usuario tenga un rol concreto.
    """

    def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere el rol: {required_role}",
            )
        return current_user

    return dependency


def require_permission(required_permission: str):
    """
    Dependencia que exige que el usuario tenga un permiso concreto.
    Usa los roles del usuario para derivar sus permisos.
    """

    def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        user_permissions = get_permissions_from_roles(current_user.roles)

        if "*" in user_permissions:
            # Rol admin o similar -> bypass
            return current_user

        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes el permiso requerido: {required_permission}",
            )
        return current_user

    return dependency
