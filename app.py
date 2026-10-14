from flask import Flask, request, jsonify
import pickle
import numpy as np

# Criando a aplicação flask

app = Flask(__name__)

# carregamento do modelo

try:
    with open("modelo_iris.pkl", "rb") as f:
        modelo = pickle.load(f)
    with open("classes_iris.pkl", "rb") as f:
        classes = pickle.load(f)
    print("modelo carregado com sucesso")
except FileNotFoundError:
    print("Erro: Arquivos do modelo não encontrados")
    modelo = None
    classes = None


@app.route("/")
def home():
    """Rota principal - informacoes da API"""
    return jsonify(
        {
            "nome": "API de Classificacao Iris",
            "versao": "1.0",
            "descricao": "API para classificar especies de flores Iris",
            "endpoints": {
                "GET /": "Informacoes da API",
                "GET /health": "Status de saude",
                "POST /predict": "Fazer previsao",
            },
            "exemplo_entrada": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        }
    )


@app.route("/health")
def health():
    """Verifica se a API está funcionando"""
    status = "healthy" if modelo is not None else "unhealthy"
    return jsonify({"status": status, "modelo_carregado": modelo is not None})


@app.route("/predict", methods=["POST"])
def predict():
    """Rota de previsão - recebe features e retorna a classe prevista
    espera um JSON com
    sepal_length
    sepal_width
    petal_length"""
    # verificar se o modelo tá carregado
    if modelo is None:
        return jsonify(
            {
                "erro": "modelo não carregado",
                "mensagem": "modelo de ml não foi inicializado corretamente",
            }
        ), 500  # Internal server error
    try:
        dados = request.get_json()
    except Exception as e:
        return jsonify(
            {
                "erro": "JSON inválido",
                "mensagem": "o corpo da requisição deve ser um JSON válido",
            }
        ), 400  # bad request
    if dados is None:
        return jsonify(
            {
                "erro": "Dados não fornecidos",
                "mensagem": "Envie um JSON com as features da flor",
            }
        ), 400
    # validar campos obrigatorios
    campos_obrigatorios = ["sepal_length", "sepal_width", "petal_lenght", "petal_width"]
    campos_faltando = [c for c in campos_obrigatorios if c not in dados]

    if campos_faltando:
        return jsonify(
            {
                "erro": "campos obrigatórios faltando",
                "campos faltando": campos_faltando,
                "campos_esperados": campos_obrigatorios,
            }
        ), 400


# Executar aplicação


if __name__ == "__main__":
    print("Iniciando API de ML")
    app.run(debug=True, port=8000)
