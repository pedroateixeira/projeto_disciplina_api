import pickle

import numpy as np
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException


class IrisRequest(BaseModel):
    """
    Modelo de Entrada - Define dados que o cliente deve enviar em /predict

    Cada campo tem:
    -tipo (float)
    -field (...)
    example - valor de exemplo no Swagger

    """

    sepal_length: float = Field(
        ..., description="Comprimento da sepala (cm)", example=1.4
    )
    sepal_width: float = Field(..., description="Largura da sepala (cm)", example=3.5)
    petal_length: float = Field(
        ..., description="Comprimento da petala (cm)", example=1.4
    )
    petal_width: float = Field(..., description="Largura da petala (cm)", example=3.5)


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


class IrisResponse(BaseModel):
    """
    Modelo de resposta - o que a API retorna para o cliente
    """

    sucesso: bool
    predicao: IrisPrediction
    probabilidades: IrisProbabilities
    entrada_recebida: IrisRequest


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
    description="API para classificar especies de flores iris utilizando machine learning e evoluindo a api flask",
    version="2.0.0",
)


@app.get("/")
def home():
    """Rota principal que retorna informaçoes sobre a API
    Util para verificar se a API esta no ar e ver os endpoints disponiveis
    teste curl http://127.0.0.1:8000]
    """
    return {
        "nome": "API de classificacao de flores iris",
        "versao": "2.0 FastAPI",
        "descricao": "API para classificar flores de iris",
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


@app.post("/predict", response_model=IrisResponse)
def predict(payload: IrisRequest) -> IrisResponse:
    """
    endpoint que recebe dados de flor e retorna a predicao
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
        predicao=IrisPrediction(
            classe=classes[predicao_idx], classe_idx=int(predicao_idx)
        ),
        probabilidades=IrisProbabilities(
            setosa=round(float(probabilidades[0]), 4),
            versicolor=round(float(probabilidades[1]), 4),
            virginica=round(float(probabilidades[2]), 4),
        ),
        entrada_recebida=payload,
    )
