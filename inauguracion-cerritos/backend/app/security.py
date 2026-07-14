"""Utilidades de seguridad: hashing de contraseñas y tokens de sesión admin."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_session_token(admin_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": admin_id,
        "email": email,
        "typ": "session",
        "iat": now,
        "exp": now + timedelta(hours=settings.session_ttl_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_admin(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    try:
        payload = jwt.decode(
            creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        if payload.get("typ") != "session":
            raise ValueError("tipo inválido")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesión expirada")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
