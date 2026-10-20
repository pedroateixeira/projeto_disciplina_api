# 🌸 Classificador de Flores Iris — API v2

API que serve um modelo de Machine Learning treinado no clássico dataset **Iris** para prever a espécie de uma flor (*setosa*, *versicolor* ou *virginica*) a partir de quatro medidas:

- comprimento da sépala (`sepal_length`)
- largura da sépala (`sepal_width`)
- comprimento da pétala (`petal_length`)
- largura da pétala (`petal_width`)

Construída com **FastAPI**, protegida por autenticação **JWT**, com **rate limiting**, **logs estruturados**, **métricas Prometheus** e uma stack de monitoramento (Prometheus + Grafana) pronta para subir com Docker Compose. Acompanha um frontend em **Streamlit** para uso interativo e usa o **uv** como gerenciador de pacotes.

> A v2 é a evolução da v1 (API única em um `main.py`): o código foi **modularizado** e ganhou predição em lote, rate limiting, alertas e dashboards. Os usuários, as senhas (via variáveis de ambiente) e a resposta do `/predict` continuam compatíveis com a v1.

---

## 📋 Índice

- [O que mudou da v1 para a v2](#o-que-mudou-da-v1-para-a-v2)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Endpoints](#endpoints)
- [Como rodar localmente](#como-rodar-localmente)
- [Autenticação e credenciais](#autenticação-e-credenciais)
- [Exemplos de uso](#exemplos-de-uso)
- [Rate limiting](#rate-limiting)
- [Métricas e monitoramento](#métricas-e-monitoramento)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Deploy no Render](#deploy-no-render)

---

## O que mudou da v1 para a v2

| Recurso                          | v1 | v2 |
|----------------------------------|:--:|:--:|
| FastAPI + JWT                    | ✅ | ✅ |
| Docker                           | ✅ | ✅ |
| Logs estruturados (JSON)         | ✅ | ✅ |
| Métricas Prometheus              | ✅ | ✅ |
| Código modularizado (routers)    | ❌ | ✅ |
| Rate limiting (slowapi)          | ❌ | ✅ |
| Predição em lote (`/predict/batch`) | ❌ | ✅ |
| Informações do modelo (`/model/info`) | ❌ | ✅ |
| CORS                             | ❌ | ✅ |
| Stack Docker Compose (API + Prometheus + Grafana) | ❌ | ✅ |
| Data source do Grafana provisionado | ❌ | ✅ |
| Alertas do Prometheus            | ✅ | ✅ (+ bloqueios por rate limit) |
| Blueprint de deploy (`render.yaml`) | ❌ | ✅ |

---

## Estrutura do projeto

```
.
├── app/
│   ├── main.py            # Cria o app, middlewares, Prometheus e inclui os routers
│   ├── core.py            # Versão da API, ambiente e logger
│   ├── schemas.py         # Modelos Pydantic (requests/responses)
│   ├── model_loader.py    # Carrega o modelo e as classes
│   ├── auth.py            # Criação/validação de tokens JWT e usuários
│   ├── rate_limit.py      # Configuração do slowapi
│   ├── metrics.py         # Métricas Prometheus customizadas
│   ├── middleware.py      # LoggingMiddleware (trace_id, latência)
│   ├── logging_config.py  # Logs em JSON
│   ├── routers/
│   │   ├── info.py        # /, /health, /model/info
│   │   ├── auth.py        # /login, /me
│   │   └── predict.py     # /predict, /predict/batch
│   └── models/
│       ├── modelo_iris.pkl    # Modelo scikit-learn treinado
│       └── classes_iris.pkl   # Nomes das classes (espécies)
├── frontend/
│   ├── streamlit_app.py   # Interface web que consome a API
│   ├── Dockerfile         # Imagem do frontend (deploy)
│   └── pyproject.toml / requirements.txt
├── prometheus/            # Configuração, alertas e Dockerfile do Prometheus
├── grafana/               # Provisionamento do data source e Dockerfile do Grafana
├── docker-compose.yml     # Stack local: API + Prometheus + Grafana
├── Dockerfile             # Imagem da API (Python 3.13)
├── render.yaml            # Blueprint do Render (API, Prometheus, Grafana, frontend)
├── pyproject.toml / uv.lock  # Dependências gerenciadas pelo uv (workspace com o frontend)
├── requirements.txt       # Exportado do uv (usado pelo Dockerfile)
└── .env.example           # Modelo das variáveis de ambiente
```

---

## Endpoints

| Método | Rota             | Autenticação | Descrição                                           |
|--------|------------------|:------------:|-----------------------------------------------------|
| GET    | `/`              | não          | Informações da API                                  |
| GET    | `/health`        | não          | Status da API e se o modelo foi carregado           |
| POST   | `/login`         | não          | Recebe usuário e senha, retorna um token JWT        |
| GET    | `/me`            | sim          | Dados do usuário autenticado                        |
| POST   | `/predict`       | sim          | Espécie prevista e probabilidades de uma flor       |
| POST   | `/predict/batch` | sim          | Predição de até 100 flores em uma única requisição  |
| GET    | `/model/info`    | sim          | Tipo do modelo, classes e features esperadas        |
| GET    | `/metrics`       | não          | Métricas no formato Prometheus                      |

A documentação interativa fica em `/docs` (Swagger) e `/redoc`. O token expira em **15 minutos** por padrão (`TOKEN_EXPIRE_MINUTES`).

---

## Como rodar localmente

### Pré-requisitos

- Docker e Docker Compose (recomendado), **ou**
- Python **3.13+** e [uv](https://docs.astral.sh/uv/) para rodar sem Docker

### 1. Configurar as variáveis de ambiente

As senhas e segredos ficam no arquivo `.env` na raiz do projeto. Ele **não é versionado** (está no `.gitignore`). Crie o seu a partir do exemplo:

```bash
cp .env.example .env
```

Preencha os valores:

```env
JWT_SECRET=uma-chave-secreta-longa
ADMIN_PASSWORD=sua-senha-admin
USER_PASSWORD=sua-senha-user
GRAFANA_PASSWORD=sua-senha-grafana
```

Para gerar um `JWT_SECRET` forte:

```bash
openssl rand -hex 32
```

### 2. Opção A — Docker Compose (API + Prometheus + Grafana)

```bash
docker compose up -d --build
```

Verifique se está tudo no ar (a API deve aparecer como `healthy`):

```bash
docker compose ps
```

| Serviço    | URL                          |
|------------|------------------------------|
| API        | http://localhost:8000        |
| Docs       | http://localhost:8000/docs   |
| Prometheus | http://localhost:9090        |
| Grafana    | http://localhost:3000 (usuário `admin`, senha = `GRAFANA_PASSWORD`) |

Para parar:

```bash
docker compose down
```

Para parar e apagar também os dados do Prometheus e do Grafana:

```bash
docker compose down -v
```

### 3. Opção B — Python com uv (sem Docker)

Instale as dependências da API e do frontend (fazem parte do mesmo workspace):

```bash
uv sync --all-packages
```

Suba a API passando o `.env` ao uvicorn:

```bash
uv run uvicorn app.main:app --reload --port 8000 --env-file .env
```

Sem o uv, use `python -m venv .venv`, ative o ambiente e rode `pip install -r requirements.txt`.

Ao adicionar uma dependência, use `uv add <pacote>` e regenere o `requirements.txt` usado pelo Docker:

```bash
uv export --no-hashes --no-emit-project --no-emit-workspace --no-dev -o requirements.txt
```

### 4. Frontend (Streamlit)

Com a API rodando, em outro terminal:

```bash
uv run streamlit run frontend/streamlit_app.py
```

Acesse http://localhost:8501, faça login e informe as medidas da flor. O frontend lê a variável `API_URL` (padrão `http://localhost:8000`).

---

## Autenticação e credenciais

A API usa **JWT**. Existem dois usuários, cujas senhas vêm das variáveis de ambiente (não há senha padrão no código):

| Usuário | Papel   | Senha (variável)  |
|---------|---------|-------------------|
| `admin` | admin   | `ADMIN_PASSWORD`  |
| `user`  | user    | `USER_PASSWORD`   |

### 🔑 Credenciais de teste

Para testar a aplicação, use:

- **Usuário:** `user`
- **Senha:** `user`

> Essas credenciais valem para o `.env` de teste (`USER_PASSWORD=user`). Em qualquer ambiente real, defina senhas fortes.

---

## Exemplos de uso

### 1. Login

```bash
curl -X POST http://localhost:8000/login -H "Content-Type: application/json" -d '{"username": "user", "password": "user"}'
```

Resposta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2. Predição individual

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -H "Authorization: Bearer SEU_TOKEN" -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```

Resposta (exemplo):

```json
{
  "sucesso": true,
  "classe": "setosa",
  "classe_idx": 0,
  "probabilidades": { "setosa": 1.0, "versicolor": 0.0, "virginica": 0.0 },
  "usuario": "user"
}
```

### 3. Predição em lote

O corpo usa a chave `items` (de 1 a 100 flores):

```bash
curl -X POST http://localhost:8000/predict/batch -H "Content-Type: application/json" -H "Authorization: Bearer SEU_TOKEN" -d '{"items": [{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}, {"sepal_length": 6.3, "sepal_width": 3.3, "petal_length": 6.0, "petal_width": 2.5}]}'
```

Resposta (exemplo):

```json
{
  "sucesso": true,
  "total": 2,
  "tempo_total_ms": 9.66,
  "predicoes": [
    { "indice": 0, "classe": "setosa", "confianca": 1.0, "probabilidades": { "setosa": 1.0, "versicolor": 0.0, "virginica": 0.0 } },
    { "indice": 1, "classe": "virginica", "confianca": 1.0, "probabilidades": { "setosa": 0.0, "versicolor": 0.0, "virginica": 1.0 } }
  ],
  "usuario": "user"
}
```

### 4. Informações do modelo

```bash
curl http://localhost:8000/model/info -H "Authorization: Bearer SEU_TOKEN"
```

---

## Rate limiting

Limites por IP, aplicados com slowapi:

| Endpoint         | Limite padrão |
|------------------|---------------|
| `/login`         | 10/minuto     |
| `/predict`       | 30/minuto     |
| `/predict/batch` | 10/minuto     |
| Demais rotas     | 60/minuto     |

Ao exceder o limite, a API responde `429` com o header `Retry-After`:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Muitas requisicoes. Limite: 10 per 1 minute",
  "retry_after_seconds": 60
}
```

Os limites podem ser alterados pelas variáveis `RATE_LIMIT_*` (veja abaixo).

---

## Métricas e monitoramento

A API expõe métricas em `/metrics`. O Prometheus coleta a cada 15 segundos e o Grafana já sobe com o data source Prometheus configurado (`http://prometheus:9090`).

### Métricas customizadas

| Métrica                                | Tipo      | Descrição                                |
|----------------------------------------|-----------|------------------------------------------|
| `iris_predictions_total`               | Counter   | Predições por `classe` e `user`          |
| `iris_batch_predictions_total`         | Counter   | Predições em lote por `user` e tamanho   |
| `login_attempts_total`                 | Counter   | Tentativas de login (`success`/`failed`) |
| `rate_limit_exceeded_total`            | Counter   | Requisições bloqueadas por rate limit    |
| `api_errors_total`                     | Counter   | Erros por endpoint e tipo                |
| `iris_prediction_latency_seconds`      | Histogram | Latência da predição individual          |
| `iris_batch_prediction_latency_seconds`| Histogram | Latência da predição em lote             |
| `model_loaded`                         | Gauge     | 1 se o modelo está carregado, 0 se não   |
| `prediction_avg_confidence`            | Gauge     | Confiança média das predições            |

Além dessas, o `prometheus-fastapi-instrumentator` publica as métricas HTTP padrão (`http_requests_total`, `http_request_duration_seconds`, etc.).

### Consultando no Prometheus

Em http://localhost:9090/graph, exemplos:

| Consulta | O que mostra |
|---|---|
| `iris_predictions_total` | Total de predições |
| `sum by (classe) (iris_predictions_total)` | Total por espécie |
| `rate(iris_predictions_total[5m])` | Predições por segundo |
| `histogram_quantile(0.95, sum by (le) (rate(iris_prediction_latency_seconds_bucket[5m])))` | Latência p95 |

### Alertas configurados

Definidos em `prometheus/alerts.yml`:

1. **APIDown** — API fora do ar por mais de 1 minuto
2. **HighErrorRate** — taxa de erros 5xx acima de 5%
3. **HighLatency** — latência p95 da predição acima de 1s
4. **ModelNotLoaded** — modelo não carregado
5. **HighRateLimitBlocks** — muitos bloqueios por rate limit

### Logs

Os logs saem em JSON no stdout, com `trace_id` por requisição (também devolvido no header `X-Trace-ID`):

```bash
docker compose logs -f api
```

---

## Variáveis de ambiente

| Variável               | Descrição                                       | Padrão                          |
|------------------------|-------------------------------------------------|---------------------------------|
| `JWT_SECRET`           | Chave usada para assinar os tokens              | — (defina no `.env`)            |
| `ADMIN_PASSWORD`       | Senha do usuário `admin`                        | — (defina no `.env`)            |
| `USER_PASSWORD`        | Senha do usuário `user`                         | — (defina no `.env`)            |
| `GRAFANA_PASSWORD`     | Senha do admin do Grafana (Docker Compose)      | — (defina no `.env`)            |
| `ENVIRONMENT`          | Nome do ambiente exibido em `/` e `/health`     | `development`                   |
| `TOKEN_EXPIRE_MINUTES` | Expiração do token JWT                          | `15`                            |
| `LOG_LEVEL`            | Nível de log                                    | `INFO`                          |
| `RATE_LIMIT_DEFAULT`   | Limite das demais rotas                         | `60/minute`                     |
| `RATE_LIMIT_PREDICT`   | Limite do `/predict`                            | `30/minute`                     |
| `RATE_LIMIT_BATCH`     | Limite do `/predict/batch`                      | `10/minute`                     |
| `RATE_LIMIT_LOGIN`     | Limite do `/login`                              | `10/minute`                     |
| `PORT`                 | Porta da API (o Render define automaticamente)  | `8000`                          |

---

## Deploy no Render

O arquivo `render.yaml` descreve quatro serviços independentes (o Render não tem `docker compose`):

| Serviço              | Descrição                         |
|----------------------|-----------------------------------|
| `api-iris-v2`        | API FastAPI                       |
| `prometheus-iris-v2` | Prometheus (scrape da API)        |
| `grafana-iris-v2`    | Grafana (dashboards)              |
| `frontend-iris-v2`   | Frontend Streamlit                |

1. No Render, vá em **Blueprints → New Blueprint Instance** e conecte este repositório.
2. Defina, no painel do Render, as variáveis marcadas como secretas: `ADMIN_PASSWORD`, `USER_PASSWORD` e `GF_SECURITY_ADMIN_PASSWORD`. O `JWT_SECRET` é gerado automaticamente.
3. O Prometheus faz scrape da API pública em `/metrics`, o Grafana usa o Prometheus como data source via `PROMETHEUS_URL` e o frontend chama a API pela variável `API_URL`.

> Se algum serviço for criado com outro nome, ajuste `API_TARGET` (Prometheus), `PROMETHEUS_URL` (Grafana) e `API_URL` (frontend) no `render.yaml`.

No plano gratuito, o primeiro acesso pode demorar alguns segundos enquanto o serviço "acorda".

---

## 📄 Licença

Projeto de estudo, disponível para fins educacionais.
