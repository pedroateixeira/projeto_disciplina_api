"""
API IRIS COM AUTENTICACAO JWT
Login + token + predicao protegida
"""

import jwt
import os
import pickle

from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SECRET_KEY = os.getenv("JWT_SECRET", "minha-chave-jwt-super-secreta")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 15

USERS_DB = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    acess_token: str
    token_type: str = "bearer"
    expires_in: int = TOKEN_EXPIRE_MINUTES * 60


class IrisPrediction(BaseModel):
    """
    Modelo de predicao - o resultado da classificacao

    contem o nome da classe prevista e seu indice numerico
    """

    classe: str = Field(..., description="Nome da especie presvista")
    classe_idx: int = Field(..., description="Indice numerico da classe")


class IrisProbabilities(BaseModel):
    """
    Modelo de probabilidades - probabilidade por classe
    """

    setosa: float
    versicolor: float
    virginica: float


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


security = HTTPBearer()


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


try:
    with open("modelo_iris.pkl", "rb") as f:
        modelo = pickle.load(f)
    with open("classes_iris.pkl", "rb") as f:
        classes = pickle.load(f)

    print("Modelo carregado com sucesso")
    MODELO_CARREGADO = True
except FileNotFoundError:
    print("ERRO: ARQUIVOS DO MODELO NAO ENCONTRADOS")
    print("VERIFIQUE SE OS ARQUIVOS .PKL ESTAO NA PASTA")
    modelo = None
    classes = None
    MODELO_CARREGADO = False


app = FastAPI(
    title="API de classificacao de flores iris",
    description="API de classificacao protegida por Token JWT",
    version="3.0.0",
    openapi_tags=[
        {"name": "Auth", "description": "Autenticacao"},
        {"name": "Predict", "description": "Predicao Protegida"},
    ],
)


@app.get("/")
def home():
    """Rota principal que retorna informaçoes sobre a API
    Util para verificar se a API esta no ar e ver os endpoints disponiveis
    teste curl http://127.0.0.1:8000]
    """
    return {
        "nome": "API de classificacao de flores iris com autentificacao",
        "versao": "3.0 com JWT",
        "descricao": "API para classificar flores de iris com autentificacao por API key",
        "endpoints": {
            "GET /": "INFORMACOES DA API",
            "GET /health": "STATUS E SAUDE DA API",
            "GET /docs": "documentacao interativa (swagger)",
            "POST /predict": "fazer a previsao ",
        },
        "modelo_carregado": MODELO_CARREGADO,
    }


@app.get("/health")
def health():
    """
    Verifica se a API esta funcionando corretamente
    """
    return {
        "status": "healthy" if MODELO_CARREGADO else "unhealthy",
        "modelo_carregado": MODELO_CARREGADO,
    }


@app.post("/login")
def login(credentials: LoginRequest):
    """
    faz o login e retorna o token JWT
    """
    user = USERS_DB.get(credentials.username)

    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="usuário ou senha incorretos")
    token = create_token(credentials.username, user["role"])
    return TokenResponse(access_token=token)


@app.get("/me", tags=["Auth"])
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Retorna infos do usuario logado
    """
    return {
        "username": current_user["role"],
        "message": "usuario atual autenticado",
    }


@app.post("/predict", response_model=IrisResponse, tags=["Predict"])
def predict(payload: IrisRequest, current_user: dict = Depends(get_current_user)):
    """
    endpoint protegido por JWT
    """
    if not MODELO_CARREGADO:
        raise HTTPException(
            status_code=503,
            detail="Modelo nao foi carregado, verifique se os arquivos .pkl existem",
        )
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

    predicao_idx = modelo.predict(features)[0]
    probabilidades = modelo.predict_proba(features)[0]

    return IrisResponse(
        sucesso=True,
        classe=classes[predicao_idx],
        classe_idx=int(predicao_idx),
        probabilidades={
            classes[i]: round(float(p), 4) for i, p in enumerate(probabilidades)
        },
        usuario=current_user["username"],
    )
