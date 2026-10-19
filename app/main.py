"""
API Iris com JWT - versao para produçao - modularizada
pronta para deploy em container/cloud
"""

import os
import pickle
import time
from pathlib import Path

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Request
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from app.auth import (
    TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_token,
    get_current_user,
)
from app.logging_config import setup_logging
from app.metrics import MODEL_LOADED, PREDICTION_LATENCY, PREDICTIONS_TOTAL
from app.middleware import LoggingMiddleware

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
API_VERSION = "4.1.0"  # versão atualizada c monitoramento

logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))


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
MODEL_LOADED.set(1 if MODELO_OK else 0)


app = FastAPI(
    title="API de classificacao de flores iris",
    description="API de classificacao com logging",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js",
)

# Adiciona Middleware de Logging (intercepta todas as requisicoes)
app.add_middleware(LoggingMiddleware)

# Instrumentacao Prometheus (adiciona metricas automaticas + endpoint /metrics)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
def home():
    """Informações da API"""
    return {
        "api": "Iris Classifier",
        "versao": API_VERSION,
        "ambiente": ENVIRONMENT,
        "modelo_carregado": MODELO_OK,
        "docs": "/docs",
        "metrics": "/metrics",
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
def predict(
    request: Request,
    payload: IrisRequest,
    current_user: dict = Depends(get_current_user),
):
    """Faz predicao (requer autenticacao)."""
    start = time.perf_counter()
    trace_id = request.state.trace_id

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
    confidence = float(max(probs))

    latency = time.perf_counter() - start

    # Metricas Prometheus
    PREDICTIONS_TOTAL.labels(classe=classe, user=current_user["username"]).inc()
    PREDICTION_LATENCY.observe(latency)

    # Log estruturado
    logger.info(
        "prediction_completed",
        extra={
            "trace_id": trace_id,
            "user": current_user["username"],
            "classe": classe,
            "confidence": round(confidence, 4),
            "latency_ms": round(latency * 1000, 2),
            "features": {
                "sepal_length": payload.sepal_length,
                "sepal_width": payload.sepal_width,
                "petal_length": payload.petal_length,
                "petal_width": payload.petal_width,
            },
        },
    )

    return IrisResponse(
        sucesso=True,
        classe=classe,
        classe_idx=int(pred_idx),
        probabilidades={classes[i]: round(float(p), 4) for i, p in enumerate(probs)},
        usuario=current_user["username"],
    )
