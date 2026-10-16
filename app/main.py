"""
API Iris com JWT - versao para produçao - modularizada
pronta para deploy em container/cloud
"""

import logging
import os
import pickle
from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

from app.auth import (
    TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_token,
    get_current_user,
)
from fastapi import Depends, FastAPI, HTTPException

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class IrisRequest(BaseModel):
    sepal_length: float = Field(
        ..., ge=0, le=10, description="Comprimento da sepala (cm)", example=1.4
    )
    sepal_width: float = Field(
        ..., ge=0, le=10, description="Largura da sepala (cm)", example=3.5
    )
    petal_length: float = Field(
        ..., ge=0, le=10, description="Comprimento da petala (cm)", example=1.4
    )
    petal_width: float = Field(
        ..., ge=0, le=10, description="Largura da petala (cm)", example=3.5
    )


class IrisResponse(BaseModel):
    sucesso: bool
    classe: str
    classe_idx: int
    probabilidades: dict[str, float]
    usuario: str


BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"

modelo = None
classes = None

try:
    with open(MODELS_DIR / "modelo_iris.pkl", "rb") as f:
        modelo = pickle.load(f)
    with open(MODELS_DIR / "classes_iris.pkl", "rb") as f:
        classes = pickle.load(f)
    logger.info(f"modelo carregado de: {MODELS_DIR}")
except FileNotFoundError:
    logger.warning("modelo nao encontrado | servico de predicao indisponivel")

MODELO_OK = modelo is not None and classes is not None


app = FastAPI(
    title="API de classificacao de flores iris",
    description="API de classificacao protegida por Token JWT para deploy em produção",
    version="4.0.0",
    openapi_tags=[
        {"name": "Auth", "description": "Autenticacao"},
        {"name": "Predict", "description": "Predicao Protegida"},
    ],
)


@app.get("/")
def home():
    """Informações da API"""
    return {
        "api": "Iris Classifier",
        "versao": "4.0.0",
        "ambiente": ENVIRONMENT,
        "modelo_carregado": MODELO_OK,
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """
    Verifica se a API esta funcionando corretamente
    """
    return {
        "status": "healthy" if MODELO_OK else "unhealthy",
        "modelo_carregado": MODELO_OK,
        "ambiente": ENVIRONMENT,
    }


@app.post("/login")
def login(credentials: LoginRequest):
    """
    faz o login e retorna o token JWT
    """
    user = authenticate_user(credentials.username, credentials.password)

    if not user:
        logger.warning(f"login falhou para: {credentials.username}")
        raise HTTPException(status_code=401, detail="usuário ou senha incorretos")
    token = create_token(credentials.username, user["role"])
    return TokenResponse(access_token=token, expires_in=TOKEN_EXPIRE_MINUTES * 60)


@app.get("/me", tags=["Auth"])
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Retorna infos do usuario logado
    """
    return current_user


@app.post("/predict", response_model=IrisResponse)
def predict(payload: IrisRequest, current_user: dict = Depends(get_current_user)):
    """Faz predicao (requer autenticacao)."""
    if not MODELO_OK:
        raise HTTPException(status_code=503, detail="Modelo nao disponivel")

    features = np.array(
        [
            [
                payload.sepal_length,
                payload.sepal_width,
                payload.petal_length,
                payload.petal_width,
            ]
        ]
    )

    pred_idx = modelo.predict(features)[0]
    probs = modelo.predict_proba(features)[0]
    classe = classes[pred_idx]

    logger.info(f"Predicao: {classe} por {current_user['username']}")

    return IrisResponse(
        sucesso=True,
        classe=classe,
        classe_idx=int(pred_idx),
        probabilidades={classes[i]: round(float(p), 4) for i, p in enumerate(probs)},
        usuario=current_user["username"],
    )
