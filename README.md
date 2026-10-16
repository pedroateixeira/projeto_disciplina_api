# 🌸 Classificador de Flores Iris

API simples que serve um modelo de Machine Learning treinado no clássico dataset **Iris** para prever a espécie de uma flor (*setosa*, *versicolor* ou *virginica*) a partir de quatro medidas:

- comprimento da sépala (`sepal_length`)
- largura da sépala (`sepal_width`)
- comprimento da pétala (`petal_length`)
- largura da pétala (`petal_width`)

A API é construída com **FastAPI**, protegida por autenticação **JWT**, e acompanha um frontend em **Streamlit** para uso interativo.

🔗 **Deploy:** https://classificador-iris.onrender.com/

> O deploy está no plano gratuito do Render, então o primeiro acesso pode demorar alguns segundos enquanto o serviço "acorda".

---

## Estrutura do projeto

```
.
├── app/
│   ├── main.py            # API FastAPI (endpoints e carregamento do modelo)
│   ├── auth.py            # Criação e validação de tokens JWT
│   └── models/
│       ├── modelo_iris.pkl   # Modelo scikit-learn treinado
│       └── classes_iris.pkl  # Nomes das classes (espécies)
├── frontend/
│   └── streamlit_app.py   # Interface web que consome a API
├── Dockerfile             # Imagem da API para deploy
├── pyproject.toml / uv.lock
└── requirements.txt
```

## Endpoints

| Método | Rota       | Autenticação | Descrição                                      |
|--------|------------|--------------|------------------------------------------------|
| GET    | `/`        | não          | Informações da API                             |
| GET    | `/health`  | não          | Status da API e se o modelo foi carregado      |
| POST   | `/login`   | não          | Recebe usuário e senha, retorna um token JWT   |
| GET    | `/me`      | sim          | Dados do usuário autenticado                   |
| POST   | `/predict` | sim          | Retorna a espécie prevista e as probabilidades |

A documentação interativa (Swagger) fica em `/docs`. O token expira em **15 minutos**.

---

## Como rodar localmente

### Pré-requisitos

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) (recomendado) ou `pip`

### 1. Instalar as dependências

Com **uv** (instala API e frontend, que fazem parte do mesmo workspace):

```bash
uv sync --all-packages
```

Ou com **pip**:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r frontend/requirements.txt
```

### 2. Configurar as variáveis de ambiente

As senhas e demais configurações ficam no arquivo `app/.env`. Ele não é versionado (está no `.gitignore`), então crie o seu a partir do exemplo abaixo:

```env
# Ambiente (development, staging, production)
ENVIRONMENT=development

# JWT
JWT_SECRET=uma-chave-secreta
TOKEN_EXPIRE_MINUTES=15

# Senhas dos usuários
ADMIN_PASSWORD=sua-senha-admin
USER_PASSWORD=user

# Porta (o Render define automaticamente)
PORT=8000
```

| Variável         | Descrição                                   |
|------------------|---------------------------------------------|
| `ENVIRONMENT`    | Nome do ambiente exibido em `/` e `/health` |
| `JWT_SECRET`     | Chave usada para assinar os tokens          |
| `ADMIN_PASSWORD` | Senha do usuário `admin`                    |
| `USER_PASSWORD`  | Senha do usuário `user`                     |
| `PORT`           | Porta da API (usada no Docker/Render)       |

O frontend lê ainda `API_URL` (padrão `http://localhost:8000`).

### 🔑 Credenciais de teste

Para testar a aplicação (local ou no deploy), use:

- **Usuário:** `user`
- **Senha:** `user`

### 3. Subir a API

Passe o `app/.env` para o uvicorn com `--env-file`:

```bash
uv run uvicorn app.main:app --reload --port 8000 --env-file app/.env
```

A API fica disponível em http://localhost:8000 e a documentação em http://localhost:8000/docs.

### 4. Subir o frontend (opcional)

Em outro terminal:

```bash
uv run streamlit run frontend/streamlit_app.py
```

Acesse http://localhost:8501, faça login e informe as medidas da flor.

### Alternativa: rodar a API com Docker

```bash
docker build -t classificador-iris .
```

```bash
docker run -p 8000:8000 --env-file app/.env classificador-iris
```

---

## Exemplo de uso via terminal

1. Fazer login e obter o token:

```bash
curl -X POST http://localhost:8000/login -H "Content-Type: application/json" -d '{"username": "user", "password": "user"}'
```

2. Fazer uma predição usando o `access_token` retornado:

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -H "Authorization: Bearer SEU_TOKEN" -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

Resposta (exemplo):

```json
{
  "sucesso": true,
  "classe": "setosa",
  "classe_idx": 0,
  "probabilidades": { "setosa": 0.98, "versicolor": 0.02, "virginica": 0.0 },
  "usuario": "user"
}
```
