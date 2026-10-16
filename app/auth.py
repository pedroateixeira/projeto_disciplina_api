"""Modulo de Autenticacao JWT
Funcoes para criar e validar tokens JWT"""

import os
from datetime import datetime, timedelta

import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastapi import Depends, HTTPException

SECRET_KEY = os.getenv("JWT_SECRET", "chave-secreta-mudar-em-prod")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 15

USERS_DB = {
    "admin": {"password": os.getenv("ADMIN_PASSWORD"), "role": "admin"},
    "user": {"password": os.getenv("USER_PASSWORD"), "role": "user"},
}

security = HTTPBearer()


def create_token(username: str, role: str) -> str:
    """
    Cria um token JWT com expiração
    """
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(security)) -> dict:
    """
    Extrai e avalia o user do token jwt
    """
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {"username": payload["sub"], "role": payload["role"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Token Expirado. Faça login de novo"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token Invalido")


def authenticate_user(username: str, password: str) -> dict | None:
    """Verifica credenciais do usuario"""
    user = USERS_DB.get(username)
    if user and user["password"] == password:
        return {"username": username, "role": user["role"]}
    return None
